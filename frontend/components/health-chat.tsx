"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ApiError, apiRequest } from "@/lib/api-client";
import { env } from "@/lib/env";

type Profile = { id: string; display_name: string; kind: string };
type Conversation = {
  id: string;
  profile_id: string;
  title: string;
  language: string;
  created_at: string;
  last_message_at: string;
};
type Citation = {
  id?: string;
  title: string;
  source: string;
  url: string;
  excerpt: string | null;
};
type Message = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  language: string;
  status: string;
  sequence: number;
  parent_message_id: string | null;
  created_at: string;
  citations: Citation[];
};
type Bootstrap = {
  profiles: Profile[];
  suggested_questions: Array<{ id: string; text: string }>;
  disclaimer: string;
  supported_languages: string[];
};

export function HealthChat() {
  const [bootstrap, setBootstrap] = useState<Bootstrap | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [profileId, setProfileId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [composer, setComposer] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [citationMessageId, setCitationMessageId] = useState<string | null>(
    null,
  );

  const loadConversations = useCallback(async () => {
    const items = await apiRequest<Conversation[]>("/chat/conversations");
    setConversations(items);
    setActiveId((current) =>
      current && items.some((item) => item.id === current)
        ? current
        : (items[0]?.id ?? null),
    );
  }, []);

  useEffect(() => {
    Promise.all([
      apiRequest<Bootstrap>("/chat/bootstrap"),
      apiRequest<Conversation[]>("/chat/conversations"),
    ])
      .then(([setup, items]) => {
        setBootstrap(setup);
        setConversations(items);
        setProfileId(setup.profiles[0]?.id ?? "");
        setActiveId(items[0]?.id ?? null);
      })
      .catch((reason) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Chat could not be loaded.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    apiRequest<Message[]>(`/chat/conversations/${activeId}/messages`)
      .then((items) => {
        setMessages(items);
        setCitationMessageId(
          [...items].reverse().find((item) => item.role === "assistant")?.id ??
            null,
        );
      })
      .catch((reason) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Messages could not be loaded.",
        ),
      );
  }, [activeId]);

  async function createConversation(initialQuestion = "") {
    if (!profileId) return;
    try {
      const created = await apiRequest<Conversation>("/chat/conversations", {
        method: "POST",
        body: JSON.stringify({
          profile_id: profileId,
          title: "New health conversation",
          language: "en",
        }),
      });
      await loadConversations();
      setActiveId(created.id);
      setMessages([]);
      setComposer(initialQuestion);
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Conversation could not be created.",
      );
    }
  }

  async function rename(item: Conversation) {
    const title = window.prompt("Rename conversation", item.title)?.trim();
    if (!title || title === item.title) return;
    try {
      await apiRequest(`/chat/conversations/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ title }),
      });
      await loadConversations();
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Conversation could not be renamed.",
      );
    }
  }

  async function remove(item: Conversation) {
    if (!window.confirm(`Delete "${item.title}" and its messages?`)) return;
    try {
      await apiRequest(`/chat/conversations/${item.id}`, { method: "DELETE" });
      if (activeId === item.id) setActiveId(null);
      await loadConversations();
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Conversation could not be deleted.",
      );
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = composer.trim();
    if (!text || !activeId || streaming) return;
    const optimistic: Message = {
      id: crypto.randomUUID(),
      conversation_id: activeId,
      role: "user",
      content: text,
      language: "en",
      status: "complete",
      sequence: (messages.at(-1)?.sequence ?? 0) + 1,
      parent_message_id: null,
      created_at: new Date().toISOString(),
      citations: [],
    };
    setMessages((items) => [...items, optimistic]);
    setComposer("");
    await consumeStream(`/chat/conversations/${activeId}/messages`, {
      content: text,
      language: "en",
    });
    await loadConversations();
  }

  async function consumeStream(path: string, body?: object) {
    if (streaming) return;
    setStreaming(true);
    setError("");
    let response = await fetch(`${env.NEXT_PUBLIC_API_URL}${path}`, {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/x-ndjson",
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (response.status === 401) {
      await fetch(`${env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      response = await fetch(`${env.NEXT_PUBLIC_API_URL}${path}`, {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/x-ndjson",
          "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
      });
    }
    if (!response.ok || !response.body) {
      setStreaming(false);
      setError("A response could not be started.");
      if (activeId)
        apiRequest<Message[]>(`/chat/conversations/${activeId}/messages`)
          .then(setMessages)
          .catch(() => undefined);
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let assistantId = "";
    try {
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.trim()) continue;
          const item = JSON.parse(line) as {
            type: string;
            message_id?: string;
            text?: string;
            message?: string;
            citation?: Citation;
          };
          if (item.type === "start" && item.message_id) {
            assistantId = item.message_id;
            const pending: Message = {
              id: assistantId,
              conversation_id: activeId ?? "",
              role: "assistant",
              content: "",
              language: "en",
              status: "pending",
              sequence: (messages.at(-1)?.sequence ?? 0) + 2,
              parent_message_id: null,
              created_at: new Date().toISOString(),
              citations: [],
            };
            setMessages((current) => [...current, pending]);
            setCitationMessageId(assistantId);
          } else if (item.type === "delta" && item.text) {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: message.content + item.text,
                      status: "streaming",
                    }
                  : message,
              ),
            );
          } else if (item.type === "citation" && item.citation) {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      citations: [
                        ...message.citations,
                        item.citation as Citation,
                      ],
                    }
                  : message,
              ),
            );
          } else if (item.type === "done") {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? { ...message, status: "complete" }
                  : message,
              ),
            );
          } else if (item.type === "error") {
            setError(item.message ?? "The response could not be completed.");
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      status: "failed",
                      content:
                        message.content ||
                        "The response could not be completed.",
                    }
                  : message,
              ),
            );
          }
        }
        if (done) break;
      }
    } catch {
      setError(
        "The streamed response was interrupted. You can regenerate it safely.",
      );
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                status: "interrupted",
                content: message.content || "The response was interrupted.",
              }
            : message,
        ),
      );
    } finally {
      setStreaming(false);
    }
  }

  async function sendFeedback(
    messageId: string,
    rating: "helpful" | "not_helpful",
  ) {
    try {
      await apiRequest(`/chat/messages/${messageId}/feedback`, {
        method: "PUT",
        body: JSON.stringify({ rating }),
      });
    } catch {
      setError("Feedback could not be saved.");
    }
  }

  async function loadOlder() {
    if (!activeId || !messages.length) return;
    const older = await apiRequest<Message[]>(
      `/chat/conversations/${activeId}/messages?before_sequence=${messages[0].sequence}&limit=40`,
    );
    setMessages((current) => [...older, ...current]);
  }

  const activeConversation =
    conversations.find((item) => item.id === activeId) ?? null;
  const citations = useMemo(
    () =>
      messages.find((item) => item.id === citationMessageId)?.citations ?? [],
    [messages, citationMessageId],
  );
  if (loading) return <ChatLoading />;
  if (!bootstrap)
    return (
      <section className="chat-error" role="alert">
        <h1>Chat is unavailable</h1>
        <p>{error}</p>
      </section>
    );

  return (
    <section className="chat-shell">
      <aside className="conversation-sidebar" aria-label="Conversations">
        <div className="sidebar-heading">
          <h1>Health education chat</h1>
          <button onClick={() => createConversation()} disabled={!profileId}>
            New
          </button>
        </div>
        <label>
          Profile
          <select
            value={profileId}
            onChange={(event) => setProfileId(event.target.value)}
          >
            {bootstrap.profiles.map((profile) => (
              <option value={profile.id} key={profile.id}>
                {profile.display_name}
              </option>
            ))}
          </select>
        </label>
        {!bootstrap.profiles.length && (
          <div className="sidebar-empty">
            <p>
              Create or request edit access to a health profile before starting
              a conversation.
            </p>
            <Link href="/profiles">Manage profiles</Link>
          </div>
        )}
        <div className="conversation-list">
          {conversations.map((item) => (
            <div className={item.id === activeId ? "active" : ""} key={item.id}>
              <button
                className="conversation-title"
                onClick={() => setActiveId(item.id)}
              >
                {item.title}
                <small>
                  {new Date(item.last_message_at).toLocaleDateString()}
                </small>
              </button>
              <button
                aria-label={`Rename ${item.title}`}
                onClick={() => rename(item)}
              >
                Edit
              </button>
              <button
                aria-label={`Delete ${item.title}`}
                onClick={() => remove(item)}
              >
                Delete
              </button>
            </div>
          ))}
          {!conversations.length && bootstrap.profiles.length > 0 && (
            <p className="sidebar-empty">No conversations yet.</p>
          )}
        </div>
      </aside>
      <section className="chat-main">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Educational support</p>
            <h2>{activeConversation?.title ?? "Start a conversation"}</h2>
          </div>
          <span className="safety-badge">Safety guidance on</span>
        </header>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="medical-chat-disclaimer">
          <b>Not medical advice.</b> {bootstrap.disclaimer}
        </div>
        {activeId ? (
          <>
            <div
              className="message-log"
              role="log"
              aria-live="polite"
              aria-busy={streaming}
            >
              {messages.length >= 40 && (
                <button className="older-button" onClick={loadOlder}>
                  Load older messages
                </button>
              )}
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onCitations={() => setCitationMessageId(message.id)}
                  onFeedback={sendFeedback}
                  onRegenerate={() =>
                    consumeStream(`/chat/messages/${message.id}/regenerate`)
                  }
                />
              ))}
              {!messages.length && (
                <Suggested
                  questions={bootstrap.suggested_questions}
                  onChoose={setComposer}
                />
              )}
            </div>
            <form className="message-composer" onSubmit={submit}>
              <label className="sr-only" htmlFor="chat-message">
                Ask a health education question
              </label>
              <textarea
                id="chat-message"
                value={composer}
                onChange={(event) => setComposer(event.target.value)}
                placeholder="Ask a general health question..."
                maxLength={4000}
                rows={2}
                disabled={streaming}
              />
              <div>
                <small>{composer.length}/4000</small>
                <button type="submit" disabled={!composer.trim() || streaming}>
                  {streaming ? "Responding..." : "Send"}
                </button>
              </div>
            </form>
          </>
        ) : (
          <Suggested
            questions={bootstrap.suggested_questions}
            onChoose={(value) => {
              void createConversation(value);
            }}
          />
        )}
      </section>
      <aside className="citations-panel" aria-label="Sources and citations">
        <h2>Sources</h2>
        <p>
          Sources support general context. They do not verify every generated
          sentence or replace professional advice.
        </p>
        {citations.length ? (
          citations.map((citation) => (
            <article key={`${citation.url}-${citation.title}`}>
              <span>{citation.source}</span>
              <h3>{citation.title}</h3>
              {citation.excerpt && <p>{citation.excerpt}</p>}
              <a href={citation.url} target="_blank" rel="noreferrer">
                Open source
              </a>
            </article>
          ))
        ) : (
          <div className="citation-empty">
            <span aria-hidden="true">i</span>
            <p>Select a response with citations to review its sources.</p>
          </div>
        )}
      </aside>
    </section>
  );
}

function SafeMarkdown({ content }: { content: string }) {
  return (
    <div className="safe-markdown">
      {content.split("\n").map((line, index) =>
        line.startsWith("## ") ? (
          <h3 key={index}>{line.slice(3)}</h3>
        ) : line.startsWith("- ") ? (
          <p className="markdown-list" key={index}>
            <span aria-hidden="true">-</span>
            {line.slice(2)}
          </p>
        ) : line ? (
          <p key={index}>{line}</p>
        ) : (
          <br key={index} />
        ),
      )}
    </div>
  );
}

function MessageBubble({
  message,
  onCitations,
  onFeedback,
  onRegenerate,
}: {
  message: Message;
  onCitations: () => void;
  onFeedback: (id: string, rating: "helpful" | "not_helpful") => void;
  onRegenerate: () => void;
}) {
  return (
    <article
      className={`chat-message ${message.role}`}
      aria-label={`${message.role} message`}
    >
      <div className="message-avatar" aria-hidden="true">
        {message.role === "assistant" ? "+" : "You"}
      </div>
      <div>
        <SafeMarkdown
          content={
            message.content ||
            (message.status === "pending" ? "Thinking..." : "")
          }
        />
        {message.role === "assistant" && message.status !== "pending" && (
          <div className="message-controls">
            <button onClick={onCitations} disabled={!message.citations.length}>
              Sources ({message.citations.length})
            </button>
            <button
              onClick={() => onFeedback(message.id, "helpful")}
              aria-label="Mark response helpful"
            >
              Helpful
            </button>
            <button
              onClick={() => onFeedback(message.id, "not_helpful")}
              aria-label="Mark response not helpful"
            >
              Not helpful
            </button>
            <button
              onClick={onRegenerate}
              disabled={message.status === "streaming"}
            >
              Regenerate
            </button>
          </div>
        )}
      </div>
    </article>
  );
}

function Suggested({
  questions,
  onChoose,
}: {
  questions: Bootstrap["suggested_questions"];
  onChoose: (value: string) => void;
}) {
  return (
    <div className="suggested-questions">
      <span aria-hidden="true">+</span>
      <h3>What would you like to understand?</h3>
      <p>
        Choose a general question or write your own. Avoid sharing details you
        do not want stored.
      </p>
      {questions.map((question) => (
        <button key={question.id} onClick={() => onChoose(question.text)}>
          {question.text}
        </button>
      ))}
    </div>
  );
}

function ChatLoading() {
  return (
    <section className="chat-loading" aria-busy="true">
      <div />
      <div />
      <div />
      <span className="sr-only">Loading conversations</span>
    </section>
  );
}

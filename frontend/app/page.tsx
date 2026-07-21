import Link from "next/link";
import { MEDICAL_DISCLAIMER } from "@/config/medical";

const features = [
  {
    icon: "AI",
    title: "Ask in everyday language",
    text: "Explore general health topics through a calm, conversational assistant that keeps important safety context visible.",
    className: "feature-blue",
  },
  {
    icon: "Sx",
    title: "Make sense of symptoms",
    text: "Organize what you are experiencing and learn which details may be useful to share with a qualified clinician.",
    className: "feature-mint",
  },
  {
    icon: "Rx",
    title: "Understand your reports",
    text: "Turn unfamiliar terms in lab results and medical documents into approachable, plain-language explanations.",
    className: "feature-sky",
  },
  {
    icon: "M",
    title: "Learn about medicines",
    text: "Review general medicine information, common precautions, and questions to discuss with a pharmacist or prescriber.",
    className: "feature-lilac",
  },
  {
    icon: "OK",
    title: "Keep care organized",
    text: "Bring reminders, personal notes, and health records together so the right information is easier to find.",
    className: "feature-leaf",
  },
  {
    icon: "i",
    title: "Check health claims",
    text: "Examine suspicious health content with source-aware context and prompts that encourage careful verification.",
    className: "feature-coral",
  },
];

const journey = [
  {
    number: "01",
    title: "Share what you need",
    text: "Ask a question, add a report, or choose a health topic using words that feel natural to you.",
  },
  {
    number: "02",
    title: "Get clear context",
    text: "Receive structured educational information with uncertainty and safety boundaries clearly shown.",
  },
  {
    number: "03",
    title: "Choose your next step",
    text: "Save useful notes, prepare questions for a professional, or seek urgent help when warning signs are present.",
  },
];

const faqs = [
  [
    "Is HealthGuard AI a doctor or diagnostic service?",
    "No. HealthGuard AI is an educational support tool. It does not diagnose conditions, prescribe treatment, or replace a doctor, pharmacist, or other qualified professional.",
  ],
  [
    "What should I do in a medical emergency?",
    "Do not wait for an online response. Contact your local emergency number or go to the nearest emergency department immediately.",
  ],
  [
    "Can it explain a medical report?",
    "It is designed to explain unfamiliar terms and help you prepare questions. A qualified clinician should interpret results in the context of your symptoms, history, and care plan.",
  ],
  [
    "How does HealthGuard AI approach misinformation?",
    "The product is designed to surface context, distinguish evidence from unsupported claims, and encourage verification through reputable sources and healthcare professionals.",
  ],
  [
    "How is my health information protected?",
    "The product is being designed around data minimization, encryption, clear controls, and transparent retention choices. Detailed privacy terms will be available before public release.",
  ],
];

export default function HomePage() {
  return (
    <>
      <section className="hero section-shell" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="pulse-dot" /> Safety-first health companion
          </p>
          <h1 id="hero-title">
            Health information should feel <span>clear, not overwhelming.</span>
          </h1>
          <p className="hero-lede">
            HealthGuard AI helps you explore symptoms, understand reports and
            medicines, organize health information, and prepare better questions
            for professional care.
          </p>
          <div className="hero-actions">
            <Link className="button" href="#get-started">
              Join the early access list <span aria-hidden="true">-&gt;</span>
            </Link>
            <Link className="text-link" href="#demo">
              See how it works <span aria-hidden="true">down</span>
            </Link>
          </div>
          <div className="hero-trust">
            <span>
              <b aria-hidden="true">OK</b> Educational, not diagnostic
            </span>
            <span>
              <b aria-hidden="true">OK</b> Privacy-minded by design
            </span>
          </div>
        </div>
        <div
          className="hero-visual"
          aria-label="Preview of the HealthGuard AI conversation experience"
        >
          <div className="orb orb-one" />
          <div className="orb orb-two" />
          <div className="app-window">
            <div className="app-bar">
              <div className="mini-brand">
                <span className="brand-mark">+</span> HealthGuard AI
              </div>
              <span className="status">
                <i /> Safety mode on
              </span>
            </div>
            <div className="conversation">
              <div className="message user-message">
                Can you help me understand what a high cholesterol result means?
              </div>
              <div className="message ai-message">
                <span className="avatar">+</span>
                <div>
                  <b>Here is a clear starting point</b>
                  <p>
                    Cholesterol results usually include several measurements.
                    Each offers a different piece of context about
                    cardiovascular health.
                  </p>
                  <div className="result-chips">
                    <span>LDL</span>
                    <span>HDL</span>
                    <span>Triglycerides</span>
                  </div>
                  <small>
                    Results should be reviewed with a clinician who knows your
                    health history.
                  </small>
                </div>
              </div>
            </div>
            <div className="composer">
              Ask a health question... <span aria-hidden="true">up</span>
            </div>
          </div>
          <div className="floating-card privacy-float">
            <span>P</span>
            <div>
              <b>Your privacy matters</b>
              <small>Designed for secure handling</small>
            </div>
          </div>
        </div>
      </section>

      <section
        className="trust-strip"
        id="trust"
        aria-label="Our trust commitments"
      >
        <div className="section-shell trust-grid">
          <p>Built around the principles healthcare deserves</p>
          <span>Clear limitations</span>
          <span>Evidence-aware context</span>
          <span>Human care comes first</span>
          <span>Privacy by design</span>
        </div>
      </section>

      <section
        className="section section-shell"
        id="features"
        aria-labelledby="features-title"
      >
        <div className="section-heading">
          <p className="eyebrow">One thoughtful companion</p>
          <h2 id="features-title">
            Support for the health moments that leave you with questions.
          </h2>
          <p>
            Tools designed to make complex information more approachable while
            keeping professional care at the center.
          </p>
        </div>
        <div className="feature-grid">
          {features.map((feature) => (
            <article
              className={`feature-card ${feature.className}`}
              key={feature.title}
            >
              <span className="feature-icon" aria-hidden="true">
                {feature.icon}
              </span>
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
              <Link
                href="#get-started"
                aria-label={`Learn more about ${feature.title}`}
              >
                Explore feature <span aria-hidden="true">-&gt;</span>
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section
        className="section demo-section"
        id="demo"
        aria-labelledby="demo-title"
      >
        <div className="section-shell split-layout">
          <div
            className="demo-device"
            aria-label="Medical report explanation preview"
          >
            <div className="report-card">
              <div className="report-top">
                <span className="file-icon">DOC</span>
                <div>
                  <b>Blood test report</b>
                  <small>Example document - 4 pages</small>
                </div>
                <span className="complete">Explained</span>
              </div>
              <div className="report-line">
                <span>LDL Cholesterol</span>
                <b>142 mg/dL</b>
              </div>
              <div className="explanation">
                <span className="avatar">+</span>
                <div>
                  <b>What this measurement describes</b>
                  <p>
                    LDL carries cholesterol through the bloodstream. Your target
                    range can vary based on your overall health and risk
                    factors.
                  </p>
                  <button type="button">Questions to ask your clinician</button>
                </div>
              </div>
            </div>
            <div className="floating-card understood">
              <strong>Plain language</strong>
              <span>Complex terms, carefully explained</span>
            </div>
          </div>
          <div className="split-copy">
            <p className="eyebrow">Reports, made approachable</p>
            <h2 id="demo-title">
              Move from unfamiliar terms to better questions.
            </h2>
            <p>
              Upload a report to explore plain-language definitions and
              understand how different measurements may fit together.
              HealthGuard AI highlights uncertainty instead of pretending every
              result has one simple meaning.
            </p>
            <ul className="check-list">
              <li>
                <span>OK</span> Clear explanations of clinical terminology
              </li>
              <li>
                <span>OK</span> Helpful questions for your next appointment
              </li>
              <li>
                <span>OK</span> Prominent context and safety reminders
              </li>
            </ul>
            <p className="microcopy">
              Always review medical results with a qualified healthcare
              professional.
            </p>
          </div>
        </div>
      </section>

      <section
        className="section emergency-section"
        aria-labelledby="emergency-title"
      >
        <div className="section-shell emergency-card">
          <div className="emergency-icon" aria-hidden="true">
            !
          </div>
          <div>
            <p className="eyebrow">When every minute matters</p>
            <h2 id="emergency-title">
              Urgent warning signs should lead to real-world help, not more
              scrolling.
            </h2>
            <p>
              Emergency guidance is designed to clearly direct people to local
              emergency services when potentially serious symptoms are
              described.
            </p>
          </div>
          <div className="emergency-note">
            <b>In an emergency</b>
            <span>Call your local emergency number now.</span>
            <small>Do not rely on an app for emergency care.</small>
          </div>
        </div>
      </section>

      <section
        className="section section-shell"
        id="privacy"
        aria-labelledby="privacy-title"
      >
        <div className="privacy-panel">
          <div className="privacy-copy">
            <p className="eyebrow light">Privacy & security</p>
            <h2 id="privacy-title">
              Your health story is personal. It should stay that way.
            </h2>
            <p>
              HealthGuard AI is being designed to collect less, protect what is
              needed, and make data controls understandable. Privacy is a
              product requirement, not a footnote.
            </p>
            <div className="security-grid">
              <div>
                <span aria-hidden="true">D</span>
                <b>Data minimization</b>
                <small>Only information needed for a chosen feature</small>
              </div>
              <div>
                <span aria-hidden="true">E</span>
                <b>Encryption</b>
                <small>Protection for data in transit and at rest</small>
              </div>
              <div>
                <span aria-hidden="true">C</span>
                <b>Clear controls</b>
                <small>Understand, export, and remove your information</small>
              </div>
              <div>
                <span aria-hidden="true">A</span>
                <b>No ad targeting</b>
                <small>Health data is not an advertising product</small>
              </div>
            </div>
          </div>
          <div className="shield-visual" aria-hidden="true">
            <div className="shield">
              <span>+</span>
            </div>
            <i className="orbit orbit-a" />
            <i className="orbit orbit-b" />
            <i className="orbit orbit-c" />
          </div>
        </div>
      </section>

      <section
        className="section journey-section"
        id="how-it-works"
        aria-labelledby="journey-title"
      >
        <div className="section-shell">
          <div className="section-heading centered">
            <p className="eyebrow">Simple by design</p>
            <h2 id="journey-title">
              From question to a more informed next step.
            </h2>
            <p>
              No jargon-filled menus. Start with what you need and move at your
              own pace.
            </p>
          </div>
          <ol className="journey-grid">
            {journey.map((step) => (
              <li key={step.number}>
                <span className="step-number">{step.number}</span>
                <div className="step-art" aria-hidden="true">
                  <span>
                    {step.number === "01"
                      ? "?"
                      : step.number === "02"
                        ? "+"
                        : "OK"}
                  </span>
                </div>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section
        className="section section-shell faq-section"
        id="faq"
        aria-labelledby="faq-title"
      >
        <div className="faq-intro">
          <p className="eyebrow">Questions, answered</p>
          <h2 id="faq-title">
            Good health technology should be easy to question.
          </h2>
          <p>
            Transparency is part of trust. Here are straightforward answers
            about what HealthGuard AI is and is not.
          </p>
          <a className="text-link" href="mailto:hello@healthguard.ai">
            Ask us something else <span aria-hidden="true">-&gt;</span>
          </a>
        </div>
        <div className="faq-list">
          {faqs.map(([question, answer]) => (
            <details key={question}>
              <summary>
                {question}
                <span aria-hidden="true">+</span>
              </summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      </section>

      <section
        className="section section-shell"
        id="get-started"
        aria-labelledby="cta-title"
      >
        <div className="cta-panel">
          <div className="cta-glow" />
          <p className="eyebrow light">A clearer way forward</p>
          <h2 id="cta-title">
            Feel more prepared for your next health conversation.
          </h2>
          <p>
            Join the early access list and help shape a health companion built
            around clarity, safety, and respect.
          </p>
          <form
            className="signup-form"
            action="mailto:hello@healthguard.ai"
            method="post"
            encType="text/plain"
          >
            <label className="sr-only" htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="Enter your email address"
              required
            />
            <button type="submit">
              Request early access <span aria-hidden="true">-&gt;</span>
            </button>
          </form>
          <small>No spam. Product updates only. Unsubscribe anytime.</small>
        </div>
      </section>

      <aside
        className="medical-banner section-shell"
        aria-label="Medical disclaimer"
      >
        <span aria-hidden="true">i</span>
        <p>
          <strong>Important medical disclaimer</strong>
          {MEDICAL_DISCLAIMER}
        </p>
      </aside>
    </>
  );
}

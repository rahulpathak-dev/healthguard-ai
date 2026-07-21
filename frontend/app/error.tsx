"use client";
import { useEffect } from "react";
export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <section>
      <h1>Something went wrong</h1>
      <p>Please try again. If the problem continues, return later.</p>
      <button onClick={reset}>Try again</button>
    </section>
  );
}

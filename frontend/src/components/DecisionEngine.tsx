import type { ClassifySuccess, DecisionStatus } from "../types";

interface DecisionEngineProps {
  status: DecisionStatus;
  result: ClassifySuccess | null;
  errorMessage: string | null;
}

function StatusBadge({ status }: { status: DecisionStatus }) {
  const labels: Record<DecisionStatus, string> = {
    ready: "Ready",
    processing: "Processing",
    completed: "Completed",
    error: "Error",
  };
  return (
    <span className={`status-badge status-${status}`} role="status">
      {status === "processing" && (
        <span className="spinner" aria-hidden="true" />
      )}
      {labels[status]}
    </span>
  );
}

export function DecisionEngine({
  status,
  result,
  errorMessage,
}: DecisionEngineProps) {
  return (
    <section className="stage-card" aria-labelledby="stage-2-title">
      <header className="stage-header">
        <span className="stage-number" aria-hidden="true">
          2
        </span>
        <h2 id="stage-2-title">Decision Engine</h2>
        <StatusBadge status={status} />
      </header>

      {status === "ready" && (
        <p className="stage-body muted">
          Waiting for a complaint. Submit from stage 1 to call the OpenAI
          Decisions API.
        </p>
      )}

      {status === "processing" && (
        <p className="stage-body">
          Sending the complaint to the Decisions API…
        </p>
      )}

      {status === "error" && (
        <div className="error-box" role="alert">
          <strong>Request failed</strong>
          <p>{errorMessage ?? "An unexpected error occurred."}</p>
        </div>
      )}

      {status === "completed" && result && (
        <dl className="tech-summary">
          <div>
            <dt>API</dt>
            <dd>OpenAI Decisions API</dd>
          </div>
          <div>
            <dt>Model</dt>
            <dd>
              <code>{result.model}</code>
            </dd>
          </div>
          <div>
            <dt>Question type</dt>
            <dd>
              <code>choice</code>
            </dd>
          </div>
          <div>
            <dt>Selected category</dt>
            <dd>
              <code>{result.category}</code>
            </dd>
          </div>
          {result.confidence !== null && result.confidence !== undefined && (
            <div>
              <dt>Confidence (API-reported estimate)</dt>
              <dd>{result.confidence.toFixed(3)}</dd>
            </div>
          )}
          {result.probabilities && result.probabilities.length > 0 && (
            <div className="probs">
              <dt>Probabilities (API-reported estimates)</dt>
              <dd>
                <ul>
                  {result.probabilities.map((p) => (
                    <li key={p.value}>
                      <code>{p.value}</code>: {p.probability.toFixed(3)}
                    </li>
                  ))}
                </ul>
              </dd>
            </div>
          )}
        </dl>
      )}
    </section>
  );
}

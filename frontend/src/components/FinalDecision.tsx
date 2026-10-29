import {
  CATEGORY_META,
  getApplicationRecommendation,
  type Category,
  type ClassifySuccess,
  type DecisionStatus,
} from "../types";

interface FinalDecisionProps {
  status: DecisionStatus;
  result: ClassifySuccess | null;
}

function CategoryIcon({ category }: { category: Category }) {
  const symbols: Record<Category, string> = {
    billing: "B",
    technical: "T",
    shipping: "S",
    other: "O",
  };
  return (
    <span className={`category-icon cat-${category}`} aria-hidden="true">
      {symbols[category]}
    </span>
  );
}

export function FinalDecision({ status, result }: FinalDecisionProps) {
  const showResult = status === "completed" && result;

  return (
    <section className="stage-card" aria-labelledby="stage-3-title">
      <header className="stage-header">
        <span className="stage-number" aria-hidden="true">
          3
        </span>
        <h2 id="stage-3-title">Final Decision</h2>
      </header>

      {!showResult && (
        <p className="stage-body muted">
          {status === "processing"
            ? "Waiting for the decision engine…"
            : status === "error"
              ? "No routing recommendation — the decision request failed."
              : "Results will appear here after a successful classification."}
        </p>
      )}

      {showResult && (
        <>
          <div className={`result-banner cat-${result.category}`}>
            <CategoryIcon category={result.category} />
            <div>
              <p className="result-label">Model classification</p>
              <p className="result-category">
                {CATEGORY_META[result.category].label}
              </p>
            </div>
          </div>

          <div className="result-block">
            <h3>What the API returned</h3>
            <p>
              Category: <strong>{CATEGORY_META[result.category].label}</strong>
            </p>
            <p className="muted">
              {CATEGORY_META[result.category].description}
            </p>
          </div>

          {(() => {
            const rec = getApplicationRecommendation(
              result.category,
              result.confidence,
            );
            return (
              <div
                className={
                  rec.needsManualReview
                    ? "result-block recommendation review"
                    : "result-block recommendation route"
                }
              >
                <h3>Application recommendation</h3>
                <p className="action-status">{rec.action}</p>
                <p className="muted">{rec.reason}</p>
                <p className="policy-note">
                  This recommendation is application policy, not the API&apos;s
                  answer. Confidence values are API-reported estimates, not
                  guarantees.
                </p>
              </div>
            );
          })()}

          <p className="demo-note" role="note">
            Demo only — no external support ticket has been created or assigned.
          </p>
        </>
      )}
    </section>
  );
}

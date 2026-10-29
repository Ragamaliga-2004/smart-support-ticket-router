import {
  MAX_COMPLAINT_LENGTH,
  SAMPLE_COMPLAINTS,
} from "../types";

interface UserInputProps {
  complaint: string;
  onComplaintChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
}

export function UserInput({
  complaint,
  onComplaintChange,
  onSubmit,
  disabled,
}: UserInputProps) {
  const length = complaint.length;
  const isEmpty = complaint.trim().length === 0;
  const isTooLong = length > MAX_COMPLAINT_LENGTH;
  const canSubmit = !disabled && !isEmpty && !isTooLong;

  return (
    <section className="stage-card" aria-labelledby="stage-1-title">
      <header className="stage-header">
        <span className="stage-number" aria-hidden="true">
          1
        </span>
        <h2 id="stage-1-title">User Input</h2>
      </header>

      <label htmlFor="complaint" className="field-label">
        Customer complaint
      </label>
      <textarea
        id="complaint"
        name="complaint"
        rows={6}
        value={complaint}
        onChange={(e) => onComplaintChange(e.target.value)}
        disabled={disabled}
        placeholder="Describe the customer's issue…"
        maxLength={MAX_COMPLAINT_LENGTH + 50}
        aria-describedby="complaint-hint complaint-count"
      />

      <div className="field-meta">
        <p id="complaint-hint" className="hint">
          {isTooLong
            ? `Maximum ${MAX_COMPLAINT_LENGTH} characters.`
            : "Enter a complaint or pick a sample below."}
        </p>
        <p
          id="complaint-count"
          className={isTooLong ? "char-count over" : "char-count"}
          aria-live="polite"
        >
          {length} / {MAX_COMPLAINT_LENGTH}
        </p>
      </div>

      <fieldset className="samples" disabled={disabled}>
        <legend>Sample complaints</legend>
        <div className="sample-list">
          {SAMPLE_COMPLAINTS.map((sample) => (
            <button
              key={sample}
              type="button"
              className="sample-btn"
              onClick={() => onComplaintChange(sample)}
            >
              {sample}
            </button>
          ))}
        </div>
      </fieldset>

      <button
        type="button"
        className="primary-btn"
        onClick={onSubmit}
        disabled={!canSubmit}
      >
        Analyze complaint
      </button>
    </section>
  );
}

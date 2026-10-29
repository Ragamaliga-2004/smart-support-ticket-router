import { useState } from "react";
import { classifyComplaint } from "./api";
import { DecisionEngine } from "./components/DecisionEngine";
import { FinalDecision } from "./components/FinalDecision";
import { UserInput } from "./components/UserInput";
import type { ClassifySuccess, DecisionStatus } from "./types";
import { MAX_COMPLAINT_LENGTH } from "./types";
import "./App.css";

export default function App() {
  const [complaint, setComplaint] = useState("");
  const [status, setStatus] = useState<DecisionStatus>("ready");
  const [result, setResult] = useState<ClassifySuccess | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isProcessing = status === "processing";

  async function handleAnalyze() {
    const trimmed = complaint.trim();
    if (!trimmed || trimmed.length > MAX_COMPLAINT_LENGTH || isProcessing) {
      return;
    }

    setStatus("processing");
    setResult(null);
    setErrorMessage(null);

    try {
      const response = await classifyComplaint(trimmed);
      if (response.success) {
        setResult(response);
        setStatus("completed");
      } else {
        setErrorMessage(response.error);
        setStatus("error");
      }
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Could not reach the backend. Is the API server running?";
      setErrorMessage(message);
      setStatus("error");
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Smart Support Ticket Router</h1>
        <p className="subtitle">
          Classifies a customer-support complaint with the OpenAI Decisions API,
          then shows a demo routing recommendation.
        </p>
      </header>

      <div className="stages" role="main">
        <UserInput
          complaint={complaint}
          onComplaintChange={setComplaint}
          onSubmit={handleAnalyze}
          disabled={isProcessing}
        />
        <DecisionEngine
          status={status}
          result={result}
          errorMessage={errorMessage}
        />
        <FinalDecision status={status} result={result} />
      </div>

      <footer className="app-footer">
        <p>
          Prototype demo — not production-ready. Classification accuracy has not
          been established against labelled test data. API access and
          billing/credits may be required.
        </p>
      </footer>
    </div>
  );
}

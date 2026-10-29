import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Smart Support Ticket Router UI", () => {
  it("shows ready state and prevents empty submission", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByText("Ready")).toBeInTheDocument();
    const analyze = screen.getByRole("button", { name: /analyze complaint/i });
    expect(analyze).toBeDisabled();

    await user.click(analyze);
    expect(screen.queryByText("Processing")).not.toBeInTheDocument();
  });

  it("shows processing state and disables duplicate submissions", async () => {
    const user = userEvent.setup();
    let resolveFetch: ((value: Response) => void) | undefined;

    vi.spyOn(globalThis, "fetch").mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        }),
    );

    render(<App />);

    await user.click(
      screen.getByRole("button", {
        name: /I was charged twice for my order\./i,
      }),
    );

    const analyze = screen.getByRole("button", { name: /analyze complaint/i });
    await user.click(analyze);

    expect(screen.getByText("Processing")).toBeInTheDocument();
    expect(analyze).toBeDisabled();
    expect(screen.getByLabelText(/customer complaint/i)).toBeDisabled();

    resolveFetch?.(
      new Response(
        JSON.stringify({
          success: true,
          category: "billing",
          confidence: 0.93,
          probabilities: null,
          model: "gpt-6-luna",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    await waitFor(() => {
      expect(screen.getByText("Completed")).toBeInTheDocument();
    });
  });

  it("shows success result and separates model vs application recommendation", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          category: "billing",
          confidence: 0.93,
          probabilities: [
            { value: "billing", probability: 0.95 },
            { value: "technical", probability: 0.02 },
            { value: "shipping", probability: 0.01 },
            { value: "other", probability: 0.02 },
          ],
          model: "gpt-6-luna",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    render(<App />);
    await user.click(
      screen.getByRole("button", {
        name: /I was charged twice for my order\./i,
      }),
    );
    await user.click(
      screen.getByRole("button", { name: /analyze complaint/i }),
    );

    await waitFor(() => {
      expect(screen.getByText("Completed")).toBeInTheDocument();
    });

    expect(screen.getByText("What the API returned")).toBeInTheDocument();
    expect(
      screen.getByText("Application recommendation"),
    ).toBeInTheDocument();
    expect(screen.getByText("Ready for billing routing")).toBeInTheDocument();
    expect(
      screen.getByText(/no external support ticket has been created/i),
    ).toBeInTheDocument();
  });

  it("shows error state when the API fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          success: false,
          error: "Decisions API returned HTTP 500.",
        }),
        { status: 502, headers: { "Content-Type": "application/json" } },
      ),
    );

    render(<App />);
    await user.click(
      screen.getByRole("button", { name: /I cannot log into my account\./i }),
    );
    await user.click(
      screen.getByRole("button", { name: /analyze complaint/i }),
    );

    await waitFor(() => {
      expect(screen.getByText("Error")).toBeInTheDocument();
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      /Decisions API returned HTTP 500/i,
    );
    expect(
      screen.queryByText("Ready for technical routing"),
    ).not.toBeInTheDocument();
  });

  it("recommends manual review when confidence is missing", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          category: "shipping",
          confidence: null,
          probabilities: null,
          model: "gpt-6-luna",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    render(<App />);
    await user.click(
      screen.getByRole("button", {
        name: /My package has not arrived/i,
      }),
    );
    await user.click(
      screen.getByRole("button", { name: /analyze complaint/i }),
    );

    await waitFor(() => {
      expect(screen.getByText("Completed")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Manual review recommended"),
    ).toBeInTheDocument();
  });
});

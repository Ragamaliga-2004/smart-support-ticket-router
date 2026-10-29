import type { ClassifyResponse } from "./types";

export async function classifyComplaint(
  complaint: string,
): Promise<ClassifyResponse> {
  const response = await fetch("/api/classify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ complaint }),
  });

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new Error("Server returned a non-JSON response.");
  }

  if (!response.ok) {
    const errorMessage =
      typeof data === "object" &&
      data !== null &&
      "error" in data &&
      typeof (data as { error: unknown }).error === "string"
        ? (data as { error: string }).error
        : `Request failed with status ${response.status}.`;
    return { success: false, error: errorMessage };
  }

  return data as ClassifyResponse;
}

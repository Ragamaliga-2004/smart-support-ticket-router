export type Category = "billing" | "technical" | "shipping" | "other";

export type DecisionStatus = "ready" | "processing" | "completed" | "error";

export interface ProbabilityItem {
  value: string;
  probability: number;
}

export interface ClassifySuccess {
  success: true;
  category: Category;
  confidence: number | null;
  probabilities: ProbabilityItem[] | null;
  model: string;
}

export interface ClassifyFailure {
  success: false;
  error: string;
  category?: null;
  confidence?: null;
  probabilities?: null;
  model?: null;
}

export type ClassifyResponse = ClassifySuccess | ClassifyFailure;

export const MAX_COMPLAINT_LENGTH = 2000;

/** Application policy threshold — not statistically validated. */
export const MANUAL_REVIEW_CONFIDENCE_THRESHOLD = 0.7;

export const CATEGORY_META: Record<
  Category,
  { label: string; description: string; routingLabel: string }
> = {
  billing: {
    label: "Billing",
    description: "Payments, duplicate charges, invoices, and refunds.",
    routingLabel: "Ready for billing routing",
  },
  technical: {
    label: "Technical",
    description: "Login problems, software errors, and product malfunctions.",
    routingLabel: "Ready for technical routing",
  },
  shipping: {
    label: "Shipping",
    description: "Delivery delays, tracking, and missing packages.",
    routingLabel: "Ready for shipping routing",
  },
  other: {
    label: "Other",
    description: "Requests that do not fit the other categories.",
    routingLabel: "Manual review recommended",
  },
};

export const SAMPLE_COMPLAINTS = [
  "I was charged twice for my order.",
  "I cannot log into my account.",
  "My package has not arrived and tracking has not updated.",
  "I would like to suggest a new product feature.",
] as const;

export function getApplicationRecommendation(
  category: Category,
  confidence: number | null,
): { action: string; needsManualReview: boolean; reason: string } {
  if (category === "other") {
    return {
      action: "Manual review recommended",
      needsManualReview: true,
      reason: "Category is 'other' — route to a human reviewer.",
    };
  }

  if (confidence === null || confidence === undefined) {
    return {
      action: "Manual review recommended",
      needsManualReview: true,
      reason:
        "API did not return confidence; application policy recommends manual review.",
    };
  }

  if (confidence < MANUAL_REVIEW_CONFIDENCE_THRESHOLD) {
    return {
      action: "Manual review recommended",
      needsManualReview: true,
      reason: `API-reported confidence (${confidence.toFixed(2)}) is below the application threshold of ${MANUAL_REVIEW_CONFIDENCE_THRESHOLD.toFixed(2)}.`,
    };
  }

  return {
    action: CATEGORY_META[category].routingLabel,
    needsManualReview: false,
    reason: `Confidence meets the application threshold of ${MANUAL_REVIEW_CONFIDENCE_THRESHOLD.toFixed(2)}.`,
  };
}

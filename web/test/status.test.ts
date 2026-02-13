import { describe, expect, it } from "vitest";

import { formatStatusLabel } from "../src/lib/status";

describe("formatStatusLabel", () => {
  it("formats lowercase status names", () => {
    expect(formatStatusLabel("queued")).toBe("Queued");
    expect(formatStatusLabel("failed")).toBe("Failed");
  });
});

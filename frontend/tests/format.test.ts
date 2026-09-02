import { describe, expect, it } from "vitest";

import { addDays, formatDuration, toCents, toMajorUnits } from "@/lib/format";

describe("formatDuration", () => {
  it("keeps sub-hour values in minutes", () => {
    expect(formatDuration(45)).toBe("45 min");
  });

  it("renders whole hours without minutes", () => {
    expect(formatDuration(120)).toBe("2 h");
  });

  it("renders hours plus the remainder", () => {
    expect(formatDuration(75)).toBe("1 h 15 min");
  });
});

describe("toCents", () => {
  it("converts a decimal amount without floating point drift", () => {
    expect(toCents("13000.45")).toBe(1300045);
  });

  it("treats invalid or negative input as zero", () => {
    expect(toCents("abc")).toBe(0);
    expect(toCents(-5)).toBe(0);
  });

  it("round-trips through toMajorUnits", () => {
    expect(toCents(toMajorUnits(1300000))).toBe(1300000);
  });
});

describe("addDays", () => {
  it("moves forward inside the same month", () => {
    expect(addDays("2026-09-10", 2)).toBe("2026-09-12");
  });

  it("rolls over a month boundary", () => {
    expect(addDays("2026-09-30", 1)).toBe("2026-10-01");
  });

  it("handles a leap day", () => {
    expect(addDays("2028-02-28", 1)).toBe("2028-02-29");
  });
});

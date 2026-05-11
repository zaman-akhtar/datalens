import "@testing-library/jest-dom/vitest";

// jsdom doesn't provide ResizeObserver — Recharts uses it.
class RO {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-expect-error attaching to window
window.ResizeObserver = window.ResizeObserver || RO;

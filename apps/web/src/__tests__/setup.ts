import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ jobId: "job-001" }),
}));

// Mock clipboard
Object.defineProperty(navigator, "clipboard", {
  value: {
    writeText: vi.fn().mockImplementation(() => Promise.resolve()),
  },
  configurable: true,
});

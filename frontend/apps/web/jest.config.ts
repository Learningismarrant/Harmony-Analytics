import type { Config } from "jest";
import nextJest from "next/jest.js";

const createJestConfig = nextJest({
  // Provide the path to your Next.js app so next/jest can load next.config.js and .env files
  dir: "./",
});

const config: Config = {
  coverageProvider: "v8",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    // Handle module aliases (matching tsconfig paths)
    "^@/(.*)$": "<rootDir>/src/$1",
    // Handle monorepo packages
    "^@harmony/api$": "<rootDir>/../../packages/api/src/index.ts",
    "^@harmony/types$": "<rootDir>/../../packages/types/src/index.ts",
    "^@harmony/ui$": "<rootDir>/../../packages/ui/src/index.ts",
  },
  testMatch: ["**/__tests__/**/*.test.{ts,tsx}"],
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/app/layout.tsx",
    "!src/app/page.tsx",
  ],
};

export default createJestConfig(config);

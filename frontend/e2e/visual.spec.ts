/**
 * Visual regression tests using Playwright toHaveScreenshot().
 *
 * Baseline screenshots are committed to e2e/snapshots/ and compared on
 * each run. To regenerate: bunx playwright test --update-snapshots
 *
 * All backend I/O is mocked — no live server required.
 */

import { test, expect } from "@playwright/test";
import { makeInitialBracket, makeCompletedBracket } from "./fixtures/bracket";

const BACKEND_WS_URL = "ws://localhost:8000/ws/simulate";
const BRACKET_API_URL = "**/api/bracket_start";

test.describe("Visual regression", () => {
  test("initial bracket state", async ({ page }) => {
    await page.route(BRACKET_API_URL, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ bracket: makeInitialBracket() }),
      }),
    );

    await page.goto("/");
    // Wait for bracketry to render
    await expect(page.getByRole("heading", { name: "March Madness Simulator" })).toBeVisible();
    // Give bracketry a moment to paint
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot("initial-state.png", { fullPage: true });
  });

  test("mid-simulation state", async ({ page }) => {
    await page.route(BRACKET_API_URL, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ bracket: makeInitialBracket() }),
      }),
    );

    // Hold the simulation open so we can screenshot "simulating" state
    let resolveHold: () => void;
    const holdPromise = new Promise<void>((resolve) => {
      resolveHold = resolve;
    });

    await page.routeWebSocket(BACKEND_WS_URL, (ws) => {
      ws.onMessage((_message) => {
        ws.send(
          JSON.stringify({
            type: "match_update",
            region: "east",
            round: "round_of_64",
            current_matchup: {
              team1: { name: "Alpha", seed: 1 },
              team2: { name: "Beta", seed: 16 },
            },
            current_winner: { name: "Alpha", seed: 1 },
          }),
        );
        // Don't send simulation_complete yet — let the test screenshot first
        holdPromise.then(() => ws.send(JSON.stringify({ type: "simulation_complete" })));
      });
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Simulate" }).click();

    // Wait for status to appear
    await expect(page.getByText("Current Region: East")).toBeVisible();

    await expect(page).toHaveScreenshot("mid-simulation.png", { fullPage: true });

    // Clean up — complete the simulation
    resolveHold!();
    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled({ timeout: 10_000 });
  });

  test("completed bracket state", async ({ page }) => {
    await page.route(BRACKET_API_URL, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ bracket: makeInitialBracket() }),
      }),
    );

    await page.routeWebSocket(BACKEND_WS_URL, (ws) => {
      ws.onMessage((_message) => {
        ws.send(
          JSON.stringify({
            type: "bracket_update",
            bracket: makeCompletedBracket(),
          }),
        );
        ws.send(JSON.stringify({ type: "simulation_complete" }));
      });
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Simulate" }).click();

    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled({ timeout: 10_000 });
    // Give confetti a moment to start
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot("completed-state.png", { fullPage: true });
  });
});

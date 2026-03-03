/**
 * E2E tests for the bracket simulation flow.
 *
 * All backend I/O is mocked:
 *   - HTTP GET /api/bracket_start → intercepted via page.route()
 *   - WS ws://localhost:8000/ws/simulate → intercepted via page.routeWebSocket()
 *
 * No real backend is required.
 */

import { test, expect } from "@playwright/test";
import { makeInitialBracket, makeCompletedBracket } from "./fixtures/bracket";

const BACKEND_WS_URL = "ws://localhost:8000/ws/simulate";
const BRACKET_API_URL = "**/api/bracket_start";

// ─── helpers ─────────────────────────────────────────────────────────────────

function mockBracketApi(page: Parameters<typeof test>[1] extends (...args: infer P) => unknown ? P[0] : never) {
  return page.route(BRACKET_API_URL, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ bracket: makeInitialBracket() }),
    }),
  );
}

// ─── tests ───────────────────────────────────────────────────────────────────

test.describe("Page load", () => {
  test("shows simulator heading and bracket", async ({ page }) => {
    await mockBracketApi(page);
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "March Madness Simulator" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled();
    await expect(page.locator("#decider")).toHaveValue("random");
  });

  test("shows all decider options", async ({ page }) => {
    await mockBracketApi(page);
    await page.goto("/");

    const decider = page.locator("#decider");
    await expect(decider.locator("option[value='random']")).toHaveText("Random");
    await expect(decider.locator("option[value='seed']")).toHaveText("Seed");
    await expect(decider.locator("option[value='ai']")).toHaveText("AI");
  });

  test("shows user preferences textarea when AI decider selected", async ({ page }) => {
    await mockBracketApi(page);
    await page.goto("/");

    await expect(page.locator("#userPreferences")).not.toBeVisible();
    await page.selectOption("#decider", "ai");
    await expect(page.locator("#userPreferences")).toBeVisible();
  });

  test("shows error when bracket API fails", async ({ page }) => {
    await page.route(BRACKET_API_URL, (route) => route.fulfill({ status: 500 }));
    await page.goto("/");

    await expect(page.getByText("Unable to load the initial bracket.")).toBeVisible();
  });
});

test.describe("Simulation flow", () => {
  test("completes full simulation with seed decider", async ({ page }) => {
    await mockBracketApi(page);

    const completedBracket = makeCompletedBracket();

    await page.routeWebSocket(BACKEND_WS_URL, (ws) => {
      ws.onMessage((_message) => {
        // Received decider config — send simulation sequence
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

        ws.send(
          JSON.stringify({
            type: "bracket_update",
            bracket: completedBracket,
          }),
        );

        ws.send(JSON.stringify({ type: "simulation_complete" }));
      });
    });

    await page.goto("/");
    await page.selectOption("#decider", "seed");
    await page.getByRole("button", { name: "Simulate" }).click();

    // Match update should be visible in simulation status panel
    const statusBox = page.locator(".simulating-box");
    await expect(statusBox.getByText("Current Region: East")).toBeVisible({ timeout: 10_000 });
    await expect(statusBox.getByText("Current Round: Round of 64")).toBeVisible();
    // Matchup card rendered with both teams
    await expect(statusBox.locator(".matchup-card")).toBeVisible();
    await expect(statusBox.getByText("VS")).toBeVisible();
    // Winner section rendered
    await expect(statusBox.getByRole("heading", { name: "Winner:" })).toBeVisible();

    // After completion, button re-enables
    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled({ timeout: 10_000 });
  });

  test("sends correct decider and preferences over WebSocket", async ({ page }) => {
    await mockBracketApi(page);

    let receivedMessage: Record<string, unknown> | null = null;

    await page.routeWebSocket(BACKEND_WS_URL, (ws) => {
      ws.onMessage((message) => {
        receivedMessage = JSON.parse(message as string) as Record<string, unknown>;
        ws.send(JSON.stringify({ type: "simulation_complete" }));
      });
    });

    await page.goto("/");
    await page.selectOption("#decider", "ai");
    await page.fill("#userPreferences", "Pick upsets");
    await page.getByRole("button", { name: "Simulate" }).click();

    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled({ timeout: 10_000 });
    expect(receivedMessage).toMatchObject({ decider: "ai", user_preferences: "Pick upsets" });
  });

  test("shows error when WebSocket connection fails", async ({ page }) => {
    await mockBracketApi(page);

    await page.routeWebSocket(BACKEND_WS_URL, (ws) => {
      ws.close();
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Simulate" }).click();

    await expect(page.getByText(/Simulation connection closed before completion/)).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled();
  });

  test("shows error message from server", async ({ page }) => {
    await mockBracketApi(page);

    await page.routeWebSocket(BACKEND_WS_URL, (ws) => {
      ws.onMessage((_message) => {
        ws.send(JSON.stringify({ error: "Rate limit exceeded" }));
      });
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Simulate" }).click();

    await expect(page.getByText("Rate limit exceeded")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled();
  });

  test("shows malformed JSON error", async ({ page }) => {
    await mockBracketApi(page);

    await page.routeWebSocket(BACKEND_WS_URL, (ws) => {
      ws.onMessage((_message) => {
        ws.send("not valid json{{{{");
      });
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Simulate" }).click();

    await expect(page.getByText("Received malformed server response.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled();
  });

  test("second simulation replaces previous state", async ({ page }) => {
    await mockBracketApi(page);

    let callCount = 0;

    await page.routeWebSocket(BACKEND_WS_URL, (ws) => {
      ws.onMessage((_message) => {
        callCount++;
        const region = callCount === 1 ? "east" : "west";
        ws.send(
          JSON.stringify({
            type: "match_update",
            region,
            round: "round_of_64",
            current_matchup: {
              team1: { name: "Alpha", seed: 1 },
              team2: { name: "Beta", seed: 16 },
            },
            current_winner: { name: "Alpha", seed: 1 },
          }),
        );
        ws.send(JSON.stringify({ type: "simulation_complete" }));
      });
    });

    await page.goto("/");

    // First simulation
    await page.getByRole("button", { name: "Simulate" }).click();
    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled({ timeout: 10_000 });
    await expect(page.getByText("Current Region: East")).toBeVisible();

    // Second simulation
    await page.getByRole("button", { name: "Simulate" }).click();
    await expect(page.getByRole("button", { name: "Simulate" })).toBeEnabled({ timeout: 10_000 });
    await expect(page.getByText("Current Region: West")).toBeVisible();
  });
});

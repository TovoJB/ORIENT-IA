import { beforeEach, describe, expect, it, vi } from "vitest";
import { sendChatMessage, sendPrediction } from "./api";

function mockFetchOnce(response: unknown, ok = true) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok,
    status: ok ? 200 : 500,
    json: async () => response,
    text: async () => JSON.stringify(response),
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("sendChatMessage", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts the message to /chat and returns the reply", async () => {
    const fetchMock = mockFetchOnce({
      reply: "Bonjour !",
      conversation_id: "abc",
    });

    const reply = await sendChatMessage("salut");
    expect(reply).toBe("Bonjour !");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/chat"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: expect.stringContaining("salut"),
      })
    );
  });

  it("throws a readable error when the API fails", async () => {
    mockFetchOnce({ detail: "boom" }, false);

    await expect(sendChatMessage("x")).rejects.toThrow("API error 500");
  });
});

describe("sendPrediction", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the prediction result", async () => {
    mockFetchOnce({
      prediction: 1,
      class_name: "versicolor",
      probabilities: [0.1, 0.8, 0.1],
    });

    const result = await sendPrediction([5.9, 3.0, 4.2, 1.5]);
    expect(result.class_name).toBe("versicolor");
    expect(result.prediction).toBe(1);
  });
});

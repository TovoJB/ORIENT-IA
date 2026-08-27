import { beforeEach, describe, expect, it, vi } from "vitest";
import { sendChatTurn, sendOrientation } from "./api";

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

describe("sendChatTurn", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts the message to /chat and returns the question payload", async () => {
    const fetchMock = mockFetchOnce({
      reply: "Quelle est votre série de baccalauréat ?",
      conversation_id: "abc",
      tools_used: [],
      question: {
        champ: "serie_bac",
        question: "Quelle est votre série de baccalauréat ?",
        multiple: false,
        options: [{ label: "Scientifique (C, D, S)", value: "s" }],
      },
      recommendation: null,
      termine: false,
    });

    const result = await sendChatTurn({ message: "Bonjour" });
    expect(result.reply).toContain("série de baccalauréat");
    expect(result.question?.champ).toBe("serie_bac");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/chat"),
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("Bonjour"),
      })
    );
  });

  it("posts an answer for a multi-choice question", async () => {
    const fetchMock = mockFetchOnce({
      reply: "Quelles compétences ?",
      conversation_id: "abc",
      tools_used: [],
      question: { champ: "competences", multiple: true, options: [] },
      recommendation: null,
      termine: false,
    });

    await sendChatTurn({
      answer: { champ: "matieres", valeur: ["mathematiques", "informatique"] },
    });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/chat"),
      expect.objectContaining({
        body: expect.stringContaining("mathematiques"),
      })
    );
  });

  it("throws a readable error when the API fails", async () => {
    mockFetchOnce({ detail: "boom" }, false);
    await expect(sendChatTurn({ message: "x" })).rejects.toThrow("API error 500");
  });
});

describe("sendOrientation", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts the profil to /orienter and returns the classement", async () => {
    const fetchMock = mockFetchOnce({
      moteur_regles: "fallback",
      ml_utilise: true,
      ml: { modele: "rf", confiance: 0.87 },
      parcours_possibles: ["isaia", "iggia"],
      classement: [
        {
          parcours: "isaia",
          categorie: "informatique",
          score_fusion: 0.8,
          proba_ml: 0.87,
          score_regles: 5,
          motifs: {
            matieres: ["mathematiques"],
            competences: [],
            interets: ["technologie"],
            metier_alignee: true,
          },
          description: "ISAIA forme des spécialistes...",
        },
      ],
      methodologie: "fusion 60/40",
    });

    const result = await sendOrientation({ serie_bac: "s" });
    expect(result.classement[0].parcours).toBe("isaia");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/orienter"),
      expect.objectContaining({ method: "POST" })
    );
  });
});

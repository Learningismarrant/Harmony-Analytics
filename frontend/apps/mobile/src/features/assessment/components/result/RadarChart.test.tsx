import { render } from "@testing-library/react-native";
import { RadarChart, type RadarDataPoint } from "./RadarChart";

const BIG_FIVE: RadarDataPoint[] = [
  { label: "Extraversion",      score: 72, niveau: "Élevé"  },
  { label: "Agreeableness",     score: 58, niveau: "Moyen"  },
  { label: "Conscientiousness", score: 85, niveau: "Élevé"  },
  { label: "Neuroticism",       score: 30, niveau: "Faible" },
  { label: "Openness",          score: 64, niveau: "Moyen"  },
];

const HMR_TRAITS: RadarDataPoint[] = [
  { label: "induction",         score: 60 },
  { label: "analogy",           score: 75 },
  { label: "matrix_reasoning",  score: 45 },
];

describe("RadarChart — rendu nominal", () => {
  it("affiche le radar pour 5 axes (Big Five)", () => {
    const { getByTestId } = render(<RadarChart data={BIG_FIVE} />);
    expect(getByTestId("radar-chart")).toBeTruthy();
  });

  it("affiche le radar pour 3 axes (QCM cognitif)", () => {
    const { getByTestId } = render(<RadarChart data={HMR_TRAITS} />);
    expect(getByTestId("radar-chart")).toBeTruthy();
  });

  it("accepte un size personnalisé", () => {
    const { getByTestId } = render(<RadarChart data={BIG_FIVE} size={300} />);
    expect(getByTestId("radar-chart")).toBeTruthy();
  });
});

describe("RadarChart — données insuffisantes", () => {
  it("affiche le message no-data pour un tableau vide", () => {
    const { getByTestId } = render(<RadarChart data={[]} />);
    expect(getByTestId("radar-no-data")).toBeTruthy();
  });

  it("affiche le message no-data pour < 3 points", () => {
    const { getByTestId } = render(
      <RadarChart data={[{ label: "X", score: 50 }, { label: "Y", score: 70 }]} />
    );
    expect(getByTestId("radar-no-data")).toBeTruthy();
  });
});

describe("RadarChart — couleurs par score", () => {
  it("accepte des scores aux seuils exacts", () => {
    const edgeCases: RadarDataPoint[] = [
      { label: "A", score: 0   },
      { label: "B", score: 40  },
      { label: "C", score: 67  },
      { label: "D", score: 100 },
    ];
    const { getByTestId } = render(<RadarChart data={edgeCases} />);
    expect(getByTestId("radar-chart")).toBeTruthy();
  });
});

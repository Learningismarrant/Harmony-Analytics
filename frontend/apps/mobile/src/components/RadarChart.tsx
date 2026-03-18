import React from 'react';
import { View, StyleSheet, Dimensions, Text as RNText } from 'react-native';
import Svg, { Polygon, Line, Circle, Text as SvgText, G } from 'react-native-svg';
import { Colors } from '../constants/Colors';
import { RadarPoint } from '@harmony/types';

const { width } = Dimensions.get('window');
const CHART_SIZE = width * 0.8; 
const CENTER = CHART_SIZE / 2;
const RADIUS = CENTER - 40; // On augmente la marge pour les labels
const MAX_SCORE = 100;

interface RadarChartProps {
  data: RadarPoint[];
}

export const RadarChart = ({ data }: RadarChartProps) => {
  if (!data || data.length === 0) {
    return <RNText style={styles.noDataText}>Aucune donnée disponible.</RNText>;
  }

  const numCategories = data.length;
  const angle = (2 * Math.PI) / numCategories;

  // Générateur de points pour une série (A ou B)
  const getPolygonPoints = (key: 'A' | 'B') => {
    return data.map((point, i) => {
      const score = point[key];
      const r = (Math.min(score, MAX_SCORE) / MAX_SCORE) * RADIUS;
      const x = CENTER + r * Math.cos(i * angle - Math.PI / 2);
      const y = CENTER + r * Math.sin(i * angle - Math.PI / 2);
      return `${x},${y}`;
    }).join(' ');
  };

  return (
    <View style={styles.chartContainer}>
      <Svg height={CHART_SIZE} width={CHART_SIZE}>
        <G>
          {/* GRILLE : Cercles concentriques */}
          {[0.2, 0.4, 0.6, 0.8, 1.0].map((ratio, index) => (
            <Circle
              key={`grid-${index}`}
              cx={CENTER}
              cy={CENTER}
              r={RADIUS * ratio}
              stroke={Colors.teak + '40'} // 40 = opacité 25%
              fill="none"
              strokeDasharray={index === 4 ? "" : "2,2"}
            />
          ))}

          {/* AXES */}
          {data.map((_, i) => {
            const x = CENTER + RADIUS * Math.cos(i * angle - Math.PI / 2);
            const y = CENTER + RADIUS * Math.sin(i * angle - Math.PI / 2);
            return (
              <Line
                key={`line-${i}`}
                x1={CENTER}
                y1={CENTER}
                x2={x}
                y2={y}
                stroke={Colors.teak + '40'}
              />
            );
          })}

          {/* SURFACE B : CIBLE (SME / Benchmark) */}
          <Polygon
            points={getPolygonPoints('B')}
            fill={`${Colors.navy}20`} // Bleu Marine très transparent
            stroke={Colors.navy}
            strokeWidth="1"
            strokeDasharray="4,2"
          />

          {/* SURFACE A : CANDIDAT (Toi) */}
          <Polygon
            points={getPolygonPoints('A')}
            fill={`${Colors.silver}80`} // Silver semi-transparent
            stroke={Colors.silver}
            strokeWidth="3"
          />

          {/* LABELS DYNAMIQUES */}
          {data.map((point, i) => {
            // Calcul de position légèrement décalé vers l'extérieur
            const labelRadius = RADIUS + 20;
            const lx = CENTER + labelRadius * Math.cos(i * angle - Math.PI / 2);
            const ly = CENTER + labelRadius * Math.sin(i * angle - Math.PI / 2);
            
            return (
              <SvgText
                key={`label-${i}`}
                x={lx}
                y={ly}
                fill={Colors.navy}
                fontSize="10"
                fontWeight="bold"
                textAnchor="middle"
                alignmentBaseline="middle"
              >
                {point.label.toUpperCase()}
              </SvgText>
            );
          })}
        </G>
      </Svg>
      
      {/* Légende rapide */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.dot, { backgroundColor: Colors.silver }]} />
          <RNText style={styles.legendText}>Vous</RNText>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.dot, { backgroundColor: Colors.navy, borderRadius: 0 }]} />
          <RNText style={styles.legendText}>Cible métier</RNText>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  chartContainer: { alignItems: 'center', justifyContent: 'center', marginVertical: 10 },
  noDataText: { textAlign: 'center', color: Colors.slate, fontSize: 12, padding: 20 },
  legend: { flexDirection: 'row', marginTop: 10, gap: 20 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  dot: { width: 10, height: 10, borderRadius: 5 },
  legendText: { fontSize: 11, color: Colors.navy, fontWeight: '600' }
});
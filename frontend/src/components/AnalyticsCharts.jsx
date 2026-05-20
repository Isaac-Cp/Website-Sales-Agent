import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
  RadialLinearScale,
} from 'chart.js';
import { Line, Bar, Doughnut, Pie, Bubble } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Common chart options for the claymorphism aesthetic
const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: 'var(--muted)',
        font: { family: 'Plus Jakarta Sans', size: 10, weight: 'bold' },
        padding: 20,
        usePointStyle: true,
        pointStyle: 'circle',
        boxWidth: 8,
        boxHeight: 8
      }
    },
    tooltip: {
      backgroundColor: 'rgba(10, 13, 20, 0.95)',
      titleFont: { family: 'Outfit', size: 13, weight: '800' },
      bodyFont: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
      padding: 16,
      cornerRadius: 16,
      displayColors: true,
      borderWidth: 1,
      borderColor: 'rgba(255, 255, 255, 0.15)',
      backdropBlur: 12,
      boxPadding: 6,
      usePointStyle: true,
      callbacks: {
        label: (context) => {
          let label = context.dataset.label || '';
          if (label) label += ': ';
          if (context.parsed.y !== null) {
            label += new Intl.NumberFormat('en-US', {
              maximumFractionDigits: 2
            }).format(context.parsed.y);
          }
          return label;
        }
      }
    }
  },
  scales: {
    x: {
      grid: { display: false, drawBorder: false },
      ticks: { 
        color: 'var(--muted)', 
        font: { family: 'Plus Jakarta Sans', size: 10, weight: '700' },
        maxRotation: 0,
        autoSkip: true,
        maxTicksLimit: 12
      }
    },
    y: {
      grid: { 
        color: 'rgba(255, 255, 255, 0.03)', 
        drawBorder: false,
        lineWidth: 1
      },
      border: { display: false },
      ticks: { 
        color: 'var(--muted)', 
        font: { family: 'Plus Jakarta Sans', size: 10, weight: '700' },
        padding: 10,
        callback: (value) => {
          if (value >= 1000) return (value / 1000) + 'k';
          return value;
        }
      }
    }
  }
};

// 1. Line graphs for multi-metric trend analysis
export const MultiMetricTrendChart = ({ data, timeRange = '7d' }) => {
  const options = {
    ...commonOptions,
    animation: { duration: 1500, easing: 'easeOutQuart' },
    plugins: {
      ...commonOptions.plugins,
      title: {
        display: false
      }
    }
  };

  const chartData = {
    labels: data?.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Sessions',
        data: data?.sessions || [120, 190, 150, 250, 220, 300, 450],
        borderColor: '#4dabff',
        backgroundColor: 'rgba(77, 171, 255, 0.08)',
        borderWidth: 3,
        pointBackgroundColor: '#4dabff',
        pointBorderColor: 'rgba(255,255,255,0.2)',
        pointHoverRadius: 6,
        pointRadius: 0,
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Conversions',
        data: data?.conversions || [12, 19, 15, 25, 22, 30, 45],
        borderColor: '#a55eea',
        backgroundColor: 'rgba(165, 94, 234, 0.08)',
        borderWidth: 3,
        pointBackgroundColor: '#a55eea',
        pointBorderColor: 'rgba(255,255,255,0.2)',
        pointHoverRadius: 6,
        pointRadius: 0,
        tension: 0.4,
        fill: true,
      }
    ]
  };

  return (
    <div className="w-full h-full" role="region" aria-label="Line graph showing sessions and conversions trends">
      <Line options={options} data={chartData} />
    </div>
  );
};

// 2. Pie charts for traffic source segmentation
export const TrafficSourceChart = ({ data }) => {
  const options = {
    ...commonOptions,
    cutout: '65%',
    plugins: {
      ...commonOptions.plugins,
      legend: {
        ...commonOptions.plugins.legend,
        position: 'right',
        align: 'center',
        labels: {
          ...commonOptions.plugins.legend.labels,
          padding: 15,
          font: { family: 'Plus Jakarta Sans', size: 9, weight: '800' }
        }
      }
    },
    animation: { animateRotate: true, animateScale: true, duration: 2000, easing: 'easeOutElastic' },
  };

  const chartData = {
    labels: ['Organic', 'Direct', 'Referral', 'Social', 'Paid'],
    datasets: [
      {
        data: data || [35, 25, 15, 15, 10],
        backgroundColor: [
          '#4dabff', 
          '#a55eea', 
          '#ff9f43', 
          '#2ed573', 
          '#ff4757'
        ],
        hoverBackgroundColor: [
          '#64baff', 
          '#b67bf2', 
          '#ffaf60', 
          '#48e085', 
          '#ff6b7a'
        ],
        borderWidth: 4,
        borderColor: 'var(--card-bg)',
        hoverOffset: 15,
        borderRadius: 10,
      }
    ]
  };

  return (
    <div className="w-full h-full" role="region" aria-label="Doughnut chart showing traffic source segmentation">
      <Doughnut options={options} data={chartData} />
    </div>
  );
};

// 3. Bar charts for side-by-side comparative performance metrics
export const ComparativePerformanceChart = ({ data }) => {
  const options = {
    ...commonOptions,
    indexAxis: 'y',
    plugins: {
      ...commonOptions.plugins,
      legend: {
        ...commonOptions.plugins.legend,
        position: 'top',
        align: 'end'
      }
    },
    scales: {
      ...commonOptions.scales,
      x: {
        ...commonOptions.scales.y,
        grid: { display: false }
      },
      y: {
        ...commonOptions.scales.x,
        grid: { display: false }
      }
    },
    animation: { duration: 1500, easing: 'easeOutQuart' },
  };

  const chartData = {
    labels: ['Sessions', 'Conversions', 'Page Views'],
    datasets: [
      {
        label: 'Previous',
        data: data?.previous || [1000, 50, 5000],
        backgroundColor: 'rgba(165, 94, 234, 0.4)',
        borderRadius: 8,
        barThickness: 12,
      },
      {
        label: 'Current',
        data: data?.current || [1200, 75, 6500],
        backgroundColor: '#4dabff',
        borderRadius: 8,
        barThickness: 12,
      }
    ]
  };

  return (
    <div className="w-full h-full" role="region" aria-label="Horizontal bar chart comparing monthly performance">
      <Bar options={options} data={chartData} />
    </div>
  );
};

// 4. Area charts to track cumulative user growth
export const CumulativeGrowthChart = ({ data }) => {
  const options = {
    ...commonOptions,
    plugins: {
      ...commonOptions.plugins,
      legend: { display: false }
    },
    animation: { duration: 2500, easing: 'easeInOutExpo' },
  };

  const chartData = {
    labels: data?.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Total Users',
        data: data?.values || [100, 250, 450, 800, 1200, 1800],
        borderColor: '#2ed573',
        backgroundColor: (context) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 300);
          gradient.addColorStop(0, 'rgba(46, 213, 115, 0.3)');
          gradient.addColorStop(1, 'rgba(46, 213, 115, 0)');
          return gradient;
        },
        fill: true,
        tension: 0.5,
        borderWidth: 4,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#2ed573',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2
      }
    ]
  };

  return (
    <div className="w-full h-full" role="region" aria-label="Area chart tracking cumulative user growth">
      <Line options={options} data={chartData} />
    </div>
  );
};

// 5. Interactive heatmaps (Bubble chart as a proxy for regional engagement)
export const GeographicEngagementChart = ({ data }) => {
  const options = {
    ...commonOptions,
    scales: {
      x: { 
        display: false,
        min: 0,
        max: 100
      },
      y: { 
        display: false,
        min: 0,
        max: 100
      }
    },
    plugins: {
      ...commonOptions.plugins,
      legend: { display: false },
      tooltip: {
        ...commonOptions.plugins.tooltip,
        callbacks: {
          label: (context) => `Density: ${context.raw.r * 2}% at Node [${context.raw.x}, ${context.raw.y}]`
        }
      }
    }
  };

  const chartData = {
    datasets: [
      {
        label: 'Engagement Density',
        data: data || [
          { x: 20, y: 30, r: 25 },
          { x: 40, y: 10, r: 15 },
          { x: 15, y: 65, r: 35 },
          { x: 75, y: 45, r: 45 },
          { x: 85, y: 85, r: 20 },
          { x: 55, y: 55, r: 30 },
          { x: 30, y: 80, r: 18 },
        ],
        backgroundColor: (context) => {
          const value = context.raw.r;
          return value > 30 ? 'rgba(77, 171, 255, 0.6)' : 'rgba(191, 149, 249, 0.5)';
        },
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        hoverBorderWidth: 2,
        hoverBorderColor: '#fff'
      }
    ]
  };

  return (
    <div className="w-full h-full relative" role="region" aria-label="Geographic engagement density heatmap">
      <div className="absolute inset-0 opacity-10 pointer-events-none grayscale invert" style={{ backgroundImage: 'url("https://www.transparenttextures.com/patterns/world-map.png")', backgroundSize: 'contain', backgroundPosition: 'center', backgroundRepeat: 'no-repeat' }}></div>
      <Bubble options={options} data={chartData} />
    </div>
  );
};

// 6. Gauge charts for real-time performance benchmarks
export const PerformanceGauge = ({ value, label, color = '#4dabff' }) => {
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '82%',
    circumference: 220,
    rotation: 250,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false }
    },
    animation: {
      duration: 2000,
      easing: 'easeOutElastic'
    }
  };

  const chartData = {
    datasets: [
      {
        data: [value, 100 - value],
        backgroundColor: [
          color,
          'rgba(255, 255, 255, 0.05)'
        ],
        borderWidth: 0,
        borderRadius: 20,
        hoverOffset: 0
      }
    ]
  };

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center" role="meter" aria-label={`${label}: ${value}%`} aria-valuemin="0" aria-valuemax="100" aria-valuenow={value}>
      <div className="w-full h-full relative">
        <Doughnut options={options} data={chartData} />
        {/* Claymorphism Inner Glow Effect for Gauge */}
        <div className="absolute inset-0 rounded-full shadow-[inset_0_0_20px_rgba(0,0,0,0.2)] pointer-events-none" style={{ margin: '15%' }}></div>
      </div>
      <div className="absolute top-[55%] text-center">
        <motion.p 
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-[var(--fs-xl)] font-black text-[var(--ink)] leading-none"
        >
          {value}%
        </motion.p>
        <p className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest mt-2">{label}</p>
      </div>
    </div>
  );
};

// Original components preserved but enhanced if needed
export const OutreachChart = ({ data }) => <MultiMetricTrendChart data={data} />;
export const NicheDistribution = ({ data }) => <TrafficSourceChart data={data?.distributions?.niches?.map(n => n.count)} />;

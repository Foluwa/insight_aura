"use client";
import { ApexOptions } from "apexcharts";
import React, { useState } from "react";
import ReactApexChart from "react-apexcharts";
import { SentimentData } from '@/types/sentiment';

interface SentimentChartProps {
  data: SentimentData;
  title?: string;
}

const SentimentChart: React.FC<SentimentChartProps> = ({ 
  data, 
  title = "Sentiment Trends" 
}) => {
  const [state] = useState({
    series: [
      {
        name: "Positive",
        data: data.positive,
      },
      {
        name: "Negative", 
        data: data.negative,
      },
      {
        name: "Neutral",
        data: data.neutral,
      },
    ],
  });

  const options: ApexOptions = {
    legend: {
      show: true,
      position: "top",
      horizontalAlign: "left",
    },
    colors: ["#10B981", "#EF4444", "#F59E0B"],
    chart: {
      fontFamily: "Satoshi, sans-serif",
      height: 335,
      type: "area",
      dropShadow: {
        enabled: true,
        color: "#623CEA14",
        top: 10,
        blur: 4,
        left: 0,
        opacity: 0.1,
      },
      toolbar: {
        show: false,
      },
    },
    responsive: [
      {
        breakpoint: 1024,
        options: {
          chart: {
            height: 300,
          },
        },
      },
      {
        breakpoint: 1366,
        options: {
          chart: {
            height: 350,
          },
        },
      },
    ],
    stroke: {
      width: [2, 2, 2],
      curve: "straight",
    },
    grid: {
      xaxis: {
        lines: {
          show: true,
        },
      },
      yaxis: {
        lines: {
          show: true,
        },
      },
    },
    dataLabels: {
      enabled: false,
    },
    markers: {
      size: 4,
      colors: "#fff",
      strokeColors: ["#10B981", "#EF4444", "#F59E0B"],
      strokeWidth: 3,
      strokeOpacity: 0.9,
      strokeDashArray: 0,
      fillOpacity: 1,
      discrete: [],
      hover: {
        size: undefined,
        sizeOffset: 5,
      },
    },
    xaxis: {
      type: "category",
      categories: [
        "Sep",
        "Oct", 
        "Nov",
        "Dec",
        "Jan",
        "Feb",
        "Mar",
      ],
      axisBorder: {
        show: false,
      },
      axisTicks: {
        show: false,
      },
    },
    yaxis: {
      title: {
        style: {
          fontSize: "0px",
        },
      },
      min: 0,
      max: 100,
    },
  };

  return (
    <div className="col-span-12 rounded-[10px] bg-white px-7.5 pb-6 pt-7.5 shadow-1 dark:bg-gray-dark dark:shadow-card xl:col-span-8">
      <div className="mb-3.5 flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h4 className="text-body-2xlg font-bold text-dark dark:text-white">
            {title}
          </h4>
        </div>
        <div className="flex items-center gap-2.5">
          <p className="font-medium uppercase text-dark dark:text-dark-6">
            Period:
          </p>
          <div className="inline-flex items-center rounded-md bg-gray-2 p-1.5 dark:bg-dark-2">
            <button className="rounded bg-white px-3 py-1 text-body-xs font-medium text-dark shadow-1 hover:bg-white hover:shadow-1 dark:bg-gray-dark dark:text-white dark:hover:bg-gray-dark">
              Day
            </button>
            <button className="rounded px-3 py-1 text-body-xs font-medium text-dark hover:bg-white hover:shadow-1 dark:text-white dark:hover:bg-gray-dark">
              Week
            </button>
            <button className="rounded px-3 py-1 text-body-xs font-medium text-dark hover:bg-white hover:shadow-1 dark:text-white dark:hover:bg-gray-dark">
              Month
            </button>
          </div>
        </div>
      </div>

      <div>
        <div className="-ml-4 -mr-5">
          <ReactApexChart
            options={options}
            series={state.series}
            type="area"
            height={310}
          />
        </div>
      </div>

      <div className="flex flex-col gap-2 text-center xsm:flex-row xsm:gap-0">
        <div className="border-stroke dark:border-dark-3 xsm:w-1/3 xsm:border-r">
          <p className="font-medium text-dark dark:text-dark-6">Positive Sentiment</p>
          <h4 className="mt-1 text-body-xl font-bold text-dark dark:text-white">
            68.4%
          </h4>
        </div>
        <div className="border-stroke dark:border-dark-3 xsm:w-1/3 xsm:border-r">
          <p className="font-medium text-dark dark:text-dark-6">Negative Sentiment</p>
          <h4 className="mt-1 text-body-xl font-bold text-dark dark:text-white">
            18.7%
          </h4>
        </div>
        <div className="xsm:w-1/3">
          <p className="font-medium text-dark dark:text-dark-6">Neutral Sentiment</p>
          <h4 className="mt-1 text-body-xl font-bold text-dark dark:text-white">
            12.9%
          </h4>
        </div>
      </div>
    </div>
  );
};

export default SentimentChart;
"use client";
import React from "react";
import ChartFive from "../Charts/ChartFive";
import ChartThree from "../Charts/ChartThree";
import ChartTwo from "../Charts/ChartTwo";
import ChatCard from "../Chat/ChatCard";
import MapOne from "../Maps/MapOne";
import DataStatsOne from "@/components/DataStats/DataStatsOne";
import ChartOne from "@/components/Charts/ChartOne";

const DetailedCharts: React.FC = () => {
  return (
    <>
      <DataStatsOne />

      <div className="mt-4 grid grid-cols-12 gap-4 md:mt-6 md:gap-6 2xl:mt-9 2xl:gap-7.5">
        <ChartOne />
        <ChartTwo />
        <ChartThree />
        <MapOne />
        <div className="col-span-12 xl:col-span-8">
        </div>
        <ChatCard />
      </div>
      <div className="grid grid-cols-12 gap-4 md:gap-6 2xl:gap-7.5 mt-4">
        <ChartThree />
        <div className="col-span-12 xl:col-span-5">
          <ChartFive />
        </div>
      </div>
    </>
  );
};

export default DetailedCharts;

import DetailedCharts from "@/components/Dashboard/Detailed-Charts";
import { Metadata } from "next";
import DefaultLayout from "@/components/Layouts/DefaultLaout";
import React from "react";

export const metadata: Metadata = {
  title: "Insight Aura | Dashboard",
  description: "",
};

export default function Home() {
  return (
    <>
      <DefaultLayout>
        <DetailedCharts />
      </DefaultLayout>
    </>
  );
}

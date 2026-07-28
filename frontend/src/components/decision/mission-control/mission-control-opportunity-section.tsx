"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { OpportunityRadar, type OpportunityRadarPoint } from "@/components/decision/mission-control/opportunity-radar";
import { WidgetShell } from "@/components/decision/mission-control/widget-shell";
import { UsChoroplethMap } from "@/components/dashboard/us-choropleth-map";
import type { UploadSummary } from "@/lib/api";

type StateMapRow = {
  state: string;
  revenue: number;
  orders?: number;
  customers?: number;
  conversion?: number;
};

type Props = {
  stateMap: StateMapRow[];
  radarPoints: OpportunityRadarPoint[];
  scopedUpload?: UploadSummary | null;
};

export function MissionControlOpportunitySection({ stateMap, radarPoints, scopedUpload }: Props) {
  const router = useRouter();

  return (
    <div className="grid items-stretch gap-6 xl:grid-cols-2">
      <div className="h-full">
        <WidgetShell
          fill
          title="Opportunity by State"
          subtitle={
            scopedUpload
              ? `Expected Total Address Revenue by geography · ${scopedUpload.file_name} only`
              : "Expected Total Address Revenue by geography"
          }
          action={
            <Link href="/market-intelligence?view=state" className="text-xs font-medium text-indigo-600 hover:underline">
              View State Intelligence →
            </Link>
          }
        >
          <UsChoroplethMap
            data={stateMap}
            mapHeight={551}
            centered
            onStateClick={(state) => router.push(`/market-intelligence?state=${encodeURIComponent(state)}`)}
          />
        </WidgetShell>
      </div>
      <div className="h-full">
        <WidgetShell
          fill
          title="Opportunity Radar"
          subtitle="Y: intelligence opportunity score · X: switch axis"
          action={
            <Link href="/opportunities" className="text-xs font-medium text-indigo-600 hover:underline">
              View All Opportunities →
            </Link>
          }
        >
          <OpportunityRadar points={radarPoints} fill chartHeight={380} />
        </WidgetShell>
      </div>
    </div>
  );
}

/** Demo placeholder metrics — used when live data is sparse or for mockup parity. */

export const PLACEHOLDER = {
  totalCustomers: 2485420,
  newCustomers: 145392,
  totalRevenue: 4782291,
  totalOrders: 1248,
  conversionRate: 0.0263,
  leFrameIncentive: 37842,
  forecastAccuracy: 0.862,
  avgPurchasePower: 72,
  avgPainIndex: 68,
  activeCampaignTargets: 892340,
  highPriorityCustomers: 412890,
  forecastRevenue: 3900000,
  forecastOrders: 1024,
  totalCost: 1200000,
  totalRoi: 2.72,
  totalCampaigns: 24,
  activeCampaigns: 6,
} as const;

export const DELTA_PLACEHOLDERS: Record<string, string> = {
  "Total Customers": "+8.4% vs Apr",
  "New Customers": "+12.7% vs Apr",
  "Total Revenue": "+23.6% vs Apr",
  "Total Orders": "+19.3% vs Apr",
  "Conversion Rate": "+0.46% vs Apr",
  "Target Customers": "+6.2% vs Apr",
  "Expected Revenue": "+18.1% vs Apr",
  "Campaign ROI": "+14.2% vs Apr",
  "Le Frame Incentive": "+18.7% MTD",
};

export const REVENUE_OVER_TIME = [
  { day: "May 1", revenue: 142000, orders: 38 },
  { day: "May 5", revenue: 168000, orders: 42 },
  { day: "May 10", revenue: 195000, orders: 48 },
  { day: "May 15", revenue: 210000, orders: 52 },
  { day: "May 20", revenue: 248000, orders: 61 },
  { day: "May 25", revenue: 276000, orders: 68 },
  { day: "May 31", revenue: 312000, orders: 74 },
];

export const TOP_CAMPAIGNS = [
  { name: "Master V9 - Spring Promotion", revenue: 1238522, roi: 3.12 },
  { name: "Master V7 - Wellness Nurture", revenue: 892400, roi: 2.84 },
  { name: "Pause M6 - Recovery Series", revenue: 654200, roi: 2.41 },
  { name: "Master V6 - Family Wellness", revenue: 521800, roi: 2.18 },
  { name: "MediSpa - Consultation Drive", revenue: 398600, roi: 1.96 },
];

export const PRODUCT_DONUT = [
  { name: "Master V9", value: 38.2 },
  { name: "Master V7", value: 22.4 },
  { name: "Master V6", value: 14.8 },
  { name: "Pause M6", value: 11.2 },
  { name: "Pause M2", value: 8.6 },
  { name: "Other", value: 4.8 },
];

export const TOP_ZIPS = [
  { zip: "75001", state: "TX", revenue: 284920, orders: 72, conversion: 0.0312 },
  { zip: "90040", state: "CA", revenue: 251380, orders: 64, conversion: 0.0288 },
  { zip: "33101", state: "FL", revenue: 198420, orders: 51, conversion: 0.0271 },
  { zip: "10001", state: "NY", revenue: 176890, orders: 45, conversion: 0.0254 },
  { zip: "60601", state: "IL", revenue: 154320, orders: 39, conversion: 0.0242 },
];

export const SEGMENT_BUBBLES = [
  { segment: "Premium Wellness", revenue: 1.2e6, conversion: 0.034 },
  { segment: "Therapeutic Wellness", revenue: 980000, conversion: 0.029 },
  { segment: "Lifestyle Wellness", revenue: 720000, conversion: 0.024 },
  { segment: "Family Wellness", revenue: 540000, conversion: 0.021 },
  { segment: "Emerging Wellness", revenue: 310000, conversion: 0.018 },
];

export const INTELLIGENCE_RADAR = [
  { axis: "Purchase Power", score: 72 },
  { axis: "Pain Index", score: 68 },
  { axis: "Lifestyle", score: 74 },
  { axis: "PRIZM Proxy", score: 65 },
  { axis: "Ceragem Segment", score: 78 },
  { axis: "Recommendation", score: 81 },
];

export const RECENT_ACTIVITY = [
  { title: "Campaign Created", detail: "Master V9 - Summer Promo", time: "May 31, 10:32 AM" },
  { title: "Campaign Report Received", detail: "Mailchimp - May Newsletter", time: "May 31, 08:15 AM" },
  { title: "New Customers Uploaded", detail: "customers_05312025.csv · 45,231 records", time: "May 31, 07:45 AM" },
  { title: "Forecast Generated", detail: "June Forecast — $5,842,000 expected", time: "May 31, 06:20 AM" },
  { title: "Recommendation Updated", detail: "Product & Campaign for 2.4M customers", time: "May 31, 05:10 AM" },
];

export const CERAGEM_SEGMENT_DONUT = [
  { name: "Premium Wellness", value: 28.1 },
  { name: "Therapeutic Wellness", value: 22.4 },
  { name: "Lifestyle Wellness", value: 18.6 },
  { name: "Family Wellness", value: 14.2 },
  { name: "Emerging Wellness", value: 10.8 },
  { name: "Opportunity", value: 5.9 },
];

export const CUSTOMERS_OVER_TIME = [
  { month: "Jan", total: 2100000, new: 98000 },
  { month: "Feb", total: 2180000, new: 102000 },
  { month: "Mar", total: 2260000, new: 108000 },
  { month: "Apr", total: 2340000, new: 129000 },
  { month: "May", total: 2485420, new: 145392 },
];

export const TOP_STATES_TABLE = [
  { state: "CA", customers: 412890, revenue: 982400 },
  { state: "TX", customers: 356420, revenue: 842100 },
  { state: "FL", customers: 298760, revenue: 698200 },
  { state: "NY", customers: 245890, revenue: 612400 },
  { state: "IL", customers: 198420, revenue: 489300 },
];

export const CAMPAIGN_ROWS = [
  { name: "Master V9 - Spring Promotion", type: "Promotion", status: "Active", target: 125000, start: "May 1", end: "May 31", forecast: 1238522 },
  { name: "Master V7 - Wellness Nurture", type: "Nurture", status: "Active", target: 98000, start: "May 5", end: "Jun 5", forecast: 892400 },
  { name: "Pause M6 - Recovery Series", type: "Consultation", status: "Scheduled", target: 72000, start: "Jun 1", end: "Jun 30", forecast: 654200 },
  { name: "Master V6 - Family Wellness", type: "Retention", status: "Draft", target: 54000, start: "—", end: "—", forecast: 521800 },
  { name: "MediSpa - Consultation Drive", type: "Consultation", status: "Completed", target: 41000, start: "Apr 1", end: "Apr 30", forecast: 398600 },
];

export const RECENT_UPLOADS = [
  { file: "customers_may_2025.csv", date: "May 31, 2025", records: 45231, status: "Completed" },
  { file: "customers_april_batch2.csv", date: "Apr 28, 2025", records: 38420, status: "Completed" },
  { file: "datalogix_enriched_q2.csv", date: "Apr 15, 2025", records: 52100, status: "Completed" },
];

export const RECOMMENDATION_ACCURACY = [
  { type: "Product Recommendation", accuracy: 0.887 },
  { type: "Message Recommendation", accuracy: 0.842 },
  { type: "Campaign Recommendation", accuracy: 0.816 },
  { type: "Geographic Recommendation", accuracy: 0.794 },
  { type: "Revenue Prediction", accuracy: 0.862 },
];

export const PRODUCT_CARDS = [
  { product: "Master V9", revenue: 1829400, change: 0.234 },
  { product: "Master V7", revenue: 1072800, change: 0.182 },
  { product: "Master V6", revenue: 708400, change: 0.124 },
  { product: "Pause M6", revenue: 536200, change: 0.098 },
  { product: "Pause M2", revenue: 412800, change: -0.042 },
];

export const ROI_OVER_TIME = [
  { month: "Jan", roi: 1.82 },
  { month: "Feb", roi: 2.04 },
  { month: "Mar", roi: 2.18 },
  { month: "Apr", roi: 2.41 },
  { month: "May", roi: 2.72 },
];

export const ROI_BY_CAMPAIGN = [
  { name: "Master V9 - Spring Promotion", roi: 3.12 },
  { name: "Master V7 - Wellness Nurture", roi: 2.84 },
  { name: "Pause M6 - Recovery Series", roi: 2.41 },
  { name: "Master V6 - Family Wellness", roi: 2.18 },
  { name: "MediSpa - Consultation Drive", roi: 1.96 },
];

export function sparklinePoints(seed = 42): number[] {
  const pts: number[] = [];
  let v = seed;
  for (let i = 0; i < 12; i++) {
    v = v * 0.92 + (i * 3.2) + (i % 3) * 2;
    pts.push(v);
  }
  return pts;
}

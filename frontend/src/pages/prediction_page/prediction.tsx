import { Link } from "react-router-dom";
import {
    Sun,
    CloudSun,
    Zap,
    Radio,
    Battery,
    Fuel,
    Cpu,
    ArrowRight,
    ArrowLeft,
    ArrowDown,
    ShieldCheck,
    IndianRupee,
    Leaf,
    Database,
    Gauge,
} from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

/* ---------- shared bits ---------- */

function Tag({
    children,
    tone = "slate",
}: {
    children: React.ReactNode;
    tone?: "orange" | "blue" | "slate" | "green";
}) {
    const tones = {
        orange: "bg-orange-50 text-[#EA580C] border-orange-100",
        blue: "bg-blue-50 text-blue-700 border-blue-100",
        slate: "bg-slate-100 text-slate-500 border-slate-200",
        green: "bg-green-50 text-green-700 border-green-100",
    };
    return (
        <span
            className={`inline-flex items-center rounded-full border px-2.5 py-1 font-mono text-[9px] font-bold uppercase tracking-[0.14em] ${tones[tone]}`}
        >
            {children}
        </span>
    );
}

function SectionLabel({ index, title }: { index: string; title: string }) {
    return (
        <div className="mb-5 flex items-baseline gap-3">
            <span className="font-mono text-xs font-bold text-orange-300">{index}</span>
            <h3 className="font-heading text-2xl font-bold tracking-tight text-slate-950">
                {title}
            </h3>
        </div>
    );
}

const forecastData = [
    { t: "H1", forecast: 3.1, actual: 3.0 },
    { t: "H2", forecast: 3.6, actual: 3.9 },
    { t: "H3", forecast: 2.4, actual: 2.1 },
    { t: "H4", forecast: 1.2, actual: 1.5 },
    { t: "H5", forecast: 0.4, actual: 0.3 },
    { t: "H6", forecast: 2.0, actual: 1.7 },
    { t: "H7", forecast: 3.3, actual: 3.5 },
    { t: "H8", forecast: 2.8, actual: 2.6 },
];

const timeline = [
    {
        hour: "Hour 1",
        icon: Radio,
        tone: "blue" as const,
        title: "Feeder available",
        body: "Cheap agricultural feeder is on. Use grid, charge battery if useful.",
    },
    {
        hour: "Hour 2",
        icon: Sun,
        tone: "orange" as const,
        title: "Solar window",
        body: "Solar supplies the load directly and tops up the battery.",
    },
    {
        hour: "Hour 3",
        icon: Battery,
        tone: "green" as const,
        title: "Feeder off",
        body: "Agricultural feeder unavailable. MPC preserves battery charge.",
    },
    {
        hour: "Hour 4",
        icon: Gauge,
        tone: "orange" as const,
        title: "Demand rises",
        body: "Pump load increases. Battery steps in to support demand.",
    },
    {
        hour: "Hour 5",
        icon: Fuel,
        tone: "slate" as const,
        title: "Grid insufficient",
        body: "Grid capacity can't cover load. Battery and diesel share the gap.",
    },
    {
        hour: "Hour 6",
        icon: Leaf,
        tone: "green" as const,
        title: "Recovery",
        body: "Solar and grid return. Battery recharges and recovers headroom.",
    },
];

const toneText: Record<string, string> = {
    blue: "text-blue-600 bg-blue-50 border-blue-100",
    orange: "text-[#EA580C] bg-orange-50 border-orange-100",
    green: "text-green-600 bg-green-50 border-green-100",
    slate: "text-slate-500 bg-slate-100 border-slate-200",
};

/* ---------- main component ---------- */

export default function PredictionForecastingSlide() {
    return (
        <div className="min-h-screen bg-white text-slate-900">
            <div className="mx-auto max-w-[1500px] px-6 py-10 sm:px-10 lg:px-16">
                {/* ===== Header ===== */}
                <header className="mb-12 flex flex-wrap items-start justify-between gap-6 border-b border-slate-200 pb-8">
                    <div>
                        <div className="flex items-center gap-2 text-[#EA580C]">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#EA580C] to-[#F7931A] text-white">
                                <Zap className="h-4 w-4" />
                            </div>
                            <span className="font-mono text-[11px] font-bold uppercase tracking-[0.16em]">
                                GRAMURJA AI
                            </span>
                        </div>
                        <h1 className="mt-4 max-w-3xl font-heading text-4xl font-bold leading-tight tracking-tight text-slate-950 sm:text-5xl">
                            AI prediction &amp; forecasting
                        </h1>
                        <p className="mt-2 max-w-2xl text-lg text-slate-500">
                            Making the microgrid future-aware
                        </p>
                    </div>
                    <div className="flex flex-col items-end gap-3">
                        <Link
                            to="/"
                            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-slate-700 shadow-sm transition-all hover:border-[#EA580C] hover:bg-orange-50 hover:text-[#EA580C]"
                        >
                            <ArrowLeft className="h-4 w-4" />
                            Back to Dashboard
                        </Link>
                        <p className="max-w-xs text-right text-sm leading-6 text-slate-400">
                            A microgrid energy mix optimizer for off-grid communities
                        </p>
                    </div>
                </header>

                {/* ===== Main pipeline visual ===== */}
                <section className="mb-14 rounded-[28px] border border-slate-200 bg-slate-50/60 p-8 sm:p-10">
                    <div className="mx-auto flex max-w-4xl flex-col items-center text-center">
                        <div className="rounded-xl border border-slate-200 bg-white px-5 py-3 shadow-sm">
                            <span className="text-sm font-semibold text-slate-700">
                                Historical data + current conditions
                            </span>
                        </div>
                        <ArrowDown className="my-2 h-5 w-5 text-slate-300" />

                        <div className="rounded-xl border border-orange-200 bg-gradient-to-br from-orange-50 to-yellow-50 px-5 py-3 shadow-sm">
                            <div className="flex items-center gap-2 text-[#EA580C]">
                                <CloudSun className="h-4 w-4" />
                                <span className="text-sm font-semibold">Forecasting layer</span>
                            </div>
                        </div>
                        <ArrowDown className="my-2 h-5 w-5 text-slate-300" />

                        <div className="grid w-full grid-cols-2 gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-4">
                            {[
                                ["Future weather", CloudSun],
                                ["Solar availability", Sun],
                                ["Load / demand", Gauge],
                                ["Feeder availability", Radio],
                            ].map(([label, Icon]) => (
                                <div key={label as string} className="flex flex-col items-center gap-2 rounded-lg bg-slate-50 px-3 py-4">
                                    {/* @ts-ignore */}
                                    <Icon className="h-5 w-5 text-slate-500" />
                                    <span className="text-center text-xs font-semibold text-slate-600">
                                        {label as string}
                                    </span>
                                </div>
                            ))}
                        </div>
                        <ArrowDown className="my-2 h-5 w-5 text-slate-300" />

                        <div className="rounded-xl border border-slate-200 bg-slate-950 px-6 py-3 text-white shadow-sm">
                            <span className="text-sm font-semibold">MPC prediction horizon</span>
                        </div>
                        <ArrowDown className="my-2 h-5 w-5 text-slate-300" />

                        <div className="rounded-xl border border-green-200 bg-green-50 px-6 py-3 shadow-sm">
                            <span className="text-sm font-semibold text-green-700">
                                Best energy decision
                            </span>
                        </div>
                        <ArrowDown className="my-2 h-5 w-5 text-slate-300" />

                        <div className="flex flex-wrap justify-center gap-3">
                            {[
                                ["Solar", Sun, "orange"],
                                ["Grid", Radio, "blue"],
                                ["Battery", Battery, "green"],
                                ["Diesel", Fuel, "slate"],
                            ].map(([label, Icon, tone]) => (
                                <div
                                    key={label as string}
                                    className={`flex items-center gap-2 rounded-full border px-4 py-2 ${toneText[tone as string]}`}
                                >
                                    {/* @ts-ignore */}
                                    <Icon className="h-4 w-4" />
                                    <span className="text-xs font-bold">{label as string}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* ===== Section 1: what do we predict ===== */}
                <section className="mb-14">
                    <SectionLabel index="01" title="What do we predict?" />
                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
                        {[
                            {
                                icon: Sun,
                                tone: "orange" as const,
                                title: "Solar / weather",
                                body: "Predict future solar-resource availability from weather information.",
                            },
                            {
                                icon: Gauge,
                                tone: "blue" as const,
                                title: "Load",
                                body: "Estimate future electricity demand from farm and community loads.",
                            },
                            {
                                icon: Radio,
                                tone: "blue" as const,
                                title: "Feeder availability",
                                body: "Use the modeled agricultural feeder schedule and village-grid conditions to anticipate when grid power is likely on.",
                            },
                            {
                                icon: Battery,
                                tone: "green" as const,
                                title: "Battery need",
                                body: "Estimate future energy shortages so MPC can decide to charge, hold, or discharge.",
                            },
                        ].map((c) => (
                            <div
                                key={c.title}
                                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_8px_24px_rgba(15,23,42,0.04)]"
                            >
                                <div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-xl border ${toneText[c.tone]}`}>
                                    <c.icon className="h-5 w-5" />
                                </div>
                                <h4 className="mb-2 font-heading text-base font-bold text-slate-950">
                                    {c.title}
                                </h4>
                                <p className="text-sm leading-6 text-slate-500">{c.body}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* ===== Section 2: data sources ===== */}
                <section className="mb-14">
                    <SectionLabel index="02" title="Our data" />
                    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                        <div className="rounded-2xl border border-blue-100 bg-blue-50/50 p-6">
                            <div className="mb-4 flex items-center gap-2">
                                <Database className="h-4 w-4 text-blue-600" />
                                <Tag tone="blue">Real data</Tag>
                            </div>
                            <ul className="space-y-3 text-sm leading-6 text-slate-700">
                                <li>Open-Meteo historical weather data</li>
                                <li>Historical weather forecast vs. actual observations</li>
                                <li>Gujarat site and weather information</li>
                                <li>Wind-resource data, used for site comparison</li>
                            </ul>
                        </div>
                        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-6">
                            <div className="mb-4 flex items-center gap-2">
                                <Cpu className="h-4 w-4 text-slate-500" />
                                <Tag tone="slate">Model input</Tag>
                            </div>
                            <ul className="space-y-3 text-sm leading-6 text-slate-700">
                                <li>Farm and community load profiles</li>
                                <li>Agricultural feeder availability schedule</li>
                                <li>Village feeder constraints</li>
                                <li>Electricity tariffs</li>
                                <li>Solar, battery, and diesel technical parameters</li>
                                <li>CAPEX assumptions</li>
                            </ul>
                        </div>
                    </div>
                    <p className="mt-4 text-xs text-slate-400">
                        Real data grounds the weather and site inputs; the rest are modeled assumptions used to represent a realistic rural microgrid, not live field measurements.
                    </p>
                </section>

                {/* ===== Section 3: forecast accuracy ===== */}
                <section className="mb-14">
                    <SectionLabel index="03" title="Forecast accuracy" />
                    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[0.8fr_1.2fr]">
                        <div className="flex flex-col justify-between rounded-2xl border border-orange-200 bg-gradient-to-br from-orange-50 to-yellow-50 p-7">
                            <div>
                                <Tag tone="orange">Forecast</Tag>
                                <div className="mt-4 font-heading text-6xl font-bold tracking-tight text-slate-950">
                                    ~17.5%
                                </div>
                                <div className="mt-1 font-mono text-xs font-bold uppercase tracking-wider text-[#EA580C]">
                                    MAE, historical weather forecast evaluation
                                </div>
                            </div>
                            <p className="mt-6 text-sm leading-6 text-slate-600">
                                Forecast error is included in our realistic MPC testing instead of assuming perfect future information.
                            </p>
                        </div>

                        <div className="rounded-2xl border border-slate-200 bg-white p-6">
                            <p className="mb-4 text-sm leading-6 text-slate-500">
                                We compare forecasted weather conditions against actual historical conditions to understand how much prediction uncertainty affects the optimizer.
                            </p>
                            <div className="h-[180px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={forecastData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                                        <XAxis dataKey="t" axisLine={false} tickLine={false} tick={{ fill: "#94A3B8", fontSize: 10 }} />
                                        <YAxis axisLine={false} tickLine={false} tick={{ fill: "#94A3B8", fontSize: 10 }} />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: "#FFFFFF",
                                                border: "1px solid #E2E8F0",
                                                borderRadius: "10px",
                                                fontSize: "11px",
                                            }}
                                        />
                                        <Line type="monotone" dataKey="forecast" stroke="#94A3B8" strokeWidth={2} strokeDasharray="4 4" dot={false} name="Forecast" />
                                        <Line type="monotone" dataKey="actual" stroke="#EA580C" strokeWidth={2.5} dot={false} name="Actual" />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="mt-3 flex gap-5 font-mono text-[10px] uppercase tracking-wider text-slate-400">
                                <span className="flex items-center gap-1.5">
                                    <span className="h-[2px] w-4 bg-slate-400" /> Forecast
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <span className="h-[2px] w-4 bg-[#EA580C]" /> Actual
                                </span>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ===== Section 4: why prediction matters ===== */}
                <section className="mb-14">
                    <SectionLabel index="04" title="Why prediction matters" />
                    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-7">
                            <Tag tone="slate">Without forecast</Tag>
                            <div className="mt-5 space-y-3">
                                {[
                                    "Current demand — react immediately",
                                    "Possible unnecessary battery discharge",
                                    "More diesel use",
                                    "Higher cost",
                                ].map((step, i) => (
                                    <div key={step} className="flex items-center gap-3">
                                        {i > 0 && <ArrowRight className="h-4 w-4 flex-shrink-0 text-slate-300" />}
                                        <span className={`text-sm ${i === 0 ? "font-semibold text-slate-800" : "text-slate-500"}`}>
                                            {step}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="rounded-2xl border border-green-200 bg-green-50/50 p-7">
                            <Tag tone="green">With forecast</Tag>
                            <div className="mt-5 space-y-3">
                                {[
                                    "Future weather + feeder + demand",
                                    "MPC looks ahead",
                                    "Preserves battery for expected shortage",
                                    "Uses cheap grid when available",
                                    "Uses solar intelligently",
                                    "Reduces diesel dependence",
                                ].map((step, i) => (
                                    <div key={step} className="flex items-center gap-3">
                                        {i > 0 && <ArrowRight className="h-4 w-4 flex-shrink-0 text-green-300" />}
                                        <span className={`text-sm ${i === 0 ? "font-semibold text-slate-800" : "text-slate-600"}`}>
                                            {step}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>

                {/* ===== Section 5: MPC look-ahead timeline ===== */}
                <section className="mb-14">
                    <SectionLabel index="05" title="MPC look-ahead example" />
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-6">
                        {timeline.map((step) => (
                            <div key={step.hour} className="rounded-xl border border-slate-200 bg-white p-4">
                                <div className="mb-3 flex items-center justify-between">
                                    <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-slate-400">
                                        {step.hour}
                                    </span>
                                    <div className={`flex h-7 w-7 items-center justify-center rounded-lg border ${toneText[step.tone]}`}>
                                        <step.icon className="h-3.5 w-3.5" />
                                    </div>
                                </div>
                                <div className="mb-1 text-sm font-bold text-slate-900">{step.title}</div>
                                <p className="text-xs leading-5 text-slate-500">{step.body}</p>
                            </div>
                        ))}
                    </div>
                    <div className="mt-6 rounded-2xl bg-slate-950 p-6 text-center">
                        <p className="mx-auto max-w-2xl text-base leading-7 text-white">
                            MPC does not ask only: "What should I do now?"<br />
                            <span className="text-orange-300">It asks: "What should I do now, considering what is likely to happen next?"</span>
                        </p>
                    </div>
                </section>

                {/* ===== Section 6: battery prediction logic ===== */}
                <section className="mb-14">
                    <SectionLabel index="06" title="Battery prediction logic" />
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        {[
                            { title: "Shortage risk low", body: "Grid or solar can be used normally.", fill: "20%" },
                            { title: "Shortage risk high", body: "Preserve battery state of charge.", fill: "85%" },
                            { title: "Feeder unavailable", body: "Discharge battery to cover load.", fill: "45%" },
                            { title: "Battery can't cover it", body: "Diesel fills the remaining deficit.", fill: "10%" },
                        ].map((s) => (
                            <div key={s.title} className="rounded-2xl border border-slate-200 bg-white p-5">
                                <div className="mb-3 flex items-center gap-2">
                                    <Battery className="h-4 w-4 text-green-600" />
                                    <span className="text-sm font-bold text-slate-900">{s.title}</span>
                                </div>
                                <div className="mb-3 h-2 overflow-hidden rounded-full bg-slate-100">
                                    <div className="h-full rounded-full bg-gradient-to-r from-green-500 to-emerald-400" style={{ width: s.fill }} />
                                </div>
                                <p className="text-xs leading-5 text-slate-500">{s.body}</p>
                            </div>
                        ))}
                    </div>
                    <p className="mt-5 text-center font-heading text-lg font-semibold text-slate-800">
                        Battery energy has future value.
                    </p>
                </section>

                {/* ===== Section 7: research finding ===== */}
                <section className="mb-14 overflow-hidden rounded-[28px] bg-slate-950 p-8 text-white sm:p-10">
                    <Tag tone="orange">Research finding</Tag>
                    <h3 className="mt-4 max-w-2xl font-heading text-2xl font-bold leading-snug sm:text-3xl">
                        Forecast-based MPC retained most of the benefit of perfect-foresight MPC.
                    </h3>

                    <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
                        {[
                            {
                                label: "Status quo",
                                sub: "No optimization",
                                reliability: "94.1%",
                                diesel: "1,080 L/yr",
                                cost: "₹167,737/yr",
                                highlight: false,
                            },
                            {
                                label: "Oracle MPC",
                                sub: "Perfect-foresight benchmark",
                                reliability: "100%",
                                diesel: "395 L/yr",
                                cost: "₹79,613/yr",
                                highlight: false,
                            },
                            {
                                label: "Forecast MPC",
                                sub: "Realistic forecast-based result",
                                reliability: "100%",
                                diesel: "197 L/yr",
                                cost: "₹58,810/yr",
                                highlight: true,
                            },
                        ].map((c) => (
                            <div
                                key={c.label}
                                className={`rounded-2xl border p-5 ${c.highlight
                                    ? "border-orange-400/40 bg-gradient-to-br from-orange-500/15 to-yellow-400/10"
                                    : "border-white/10 bg-white/[0.04]"
                                    }`}
                            >
                                <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                                    {c.sub}
                                </div>
                                <div className="mt-1 font-heading text-lg font-bold text-white">{c.label}</div>
                                <div className="mt-5 space-y-3">
                                    <div className="flex items-center justify-between">
                                        <span className="flex items-center gap-1.5 text-xs text-slate-400">
                                            <ShieldCheck className="h-3.5 w-3.5" /> Reliability
                                        </span>
                                        <span className={`font-mono text-sm font-bold ${c.highlight ? "text-orange-300" : "text-white"}`}>
                                            {c.reliability}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="flex items-center gap-1.5 text-xs text-slate-400">
                                            <Fuel className="h-3.5 w-3.5" /> Diesel
                                        </span>
                                        <span className={`font-mono text-sm font-bold ${c.highlight ? "text-orange-300" : "text-white"}`}>
                                            {c.diesel}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="flex items-center gap-1.5 text-xs text-slate-400">
                                            <IndianRupee className="h-3.5 w-3.5" /> Cost
                                        </span>
                                        <span className={`font-mono text-sm font-bold ${c.highlight ? "text-orange-300" : "text-white"}`}>
                                            {c.cost}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* ===== Section 8: end-to-end flow ===== */}
                <section className="mb-6">
                    <SectionLabel index="07" title="End-to-end prediction flow" />
                    <div className="flex flex-wrap items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-slate-50/60 p-7">
                        {[
                            "Real weather",
                            "Weather / solar forecast",
                            "Load + feeder forecast",
                            "MPC future horizon",
                            "Optimal dispatch",
                            "Solar + grid + battery + diesel",
                            "Reliability + cost + CO₂",
                        ].map((step, i, arr) => (
                            <div key={step} className="flex items-center gap-3">
                                <div className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-center text-xs font-semibold text-slate-700 shadow-sm">
                                    {step}
                                </div>
                                {i < arr.length - 1 && <ArrowRight className="h-4 w-4 flex-shrink-0 text-slate-300" />}
                            </div>
                        ))}
                    </div>
                </section>

                {/* ===== Final message ===== */}
                <section className="rounded-2xl border border-orange-100 bg-gradient-to-r from-orange-50 to-yellow-50 p-8 text-center">
                    <p className="font-heading text-xl font-bold leading-snug text-slate-900 sm:text-2xl">
                        Prediction gives MPC foresight.{" "}
                        <span className="text-[#EA580C]">MPC converts foresight into action.</span>
                    </p>
                </section>
            </div>
        </div>
    );
}
"use client";

import { motion } from "framer-motion";
import {
  Cpu,
  Database,
  BrainCircuit,
  Cloud,
  Server,
  ShieldCheck,
  Zap,
  Workflow,
} from "lucide-react";

const stack = [
  {
    title: "Frontend",
    value: "Next.js 15",
    icon: Cpu,
    color: "text-cyan-400",
  },
  {
    title: "Backend",
    value: "FastAPI",
    icon: Server,
    color: "text-emerald-400",
  },
  {
    title: "AI Runtime",
    value: "HuggingFace",
    icon: BrainCircuit,
    color: "text-violet-400",
  },
  {
    title: "Database",
    value: "SQLite / PostgreSQL",
    icon: Database,
    color: "text-blue-400",
  },
  {
    title: "Deployment",
    value: "Docker",
    icon: Cloud,
    color: "text-orange-400",
  },
  {
    title: "Security",
    value: "JWT + HTTPS",
    icon: ShieldCheck,
    color: "text-green-400",
  },
];
export default function TechnologyStack() {

return (

<section
className="relative overflow-hidden bg-[#040611] py-32"
>

<div className="mx-auto max-w-7xl px-6">

<div className="mb-20 text-center">

<span className="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-4 py-2 text-cyan-300">
Runtime Infrastructure
</span>

<h2 className="mt-6 text-5xl font-bold text-white">

Powered by a Modern

<span className="bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-transparent">
{" "}AI Stack
</span>

</h2>

</div>
<div className="grid gap-8 md:grid-cols-2 xl:grid-cols-3">

{stack.map((item,index)=>{

const Icon=item.icon;

return(

<motion.div

key={item.title}

initial={{opacity:0,y:30}}

whileInView={{opacity:1,y:0}}

transition={{delay:index*0.15}}

viewport={{once:true}}

whileHover={{
scale:1.03,
y:-8,
}}

className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl"

>

<div className={`mb-6 ${item.color}`}>

<Icon size={42}/>

</div>

<h3 className="text-xl font-semibold text-white">

{item.title}

</h3>

<p className="mt-3 text-gray-400">

{item.value}

</p>

</motion.div>

)

})}

</div>
<div className="mt-24 rounded-[32px] border border-cyan-500/20 bg-white/5 p-10">

<h3 className="mb-10 text-3xl font-bold text-white">

Runtime Engine

</h3>

<div className="flex flex-wrap items-center justify-center gap-6">

{[
"Upload",
"Parser",
"Reasoning",
"Planning",
"Rendering",
"Export"
].map((step,index)=>(

<div
key={step}
className="flex items-center"
>

<div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-4">

<span className="text-white">

{step}

</span>

</div>

{index!==5&&(

<Workflow className="mx-4 text-cyan-400"/>

)}

</div>

))}

</div>

</div>
</div>
</section>

);

}
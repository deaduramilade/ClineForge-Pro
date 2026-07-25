"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Upload,
  FileSearch,
  BrainCircuit,
  Camera,
  Images,
  CheckCircle2,
} from "lucide-react";
const steps = [
  {
    title: "Uploading Screenplay",
    icon: Upload,
  },
  {
    title: "Parsing Script",
    icon: FileSearch,
  },
  {
    title: "Reasoning",
    icon: BrainCircuit,
  },
  {
    title: "Planning Camera",
    icon: Camera,
  },
  {
    title: "Generating Storyboards",
    icon: Images,
  },
  {
    title: "Completed",
    icon: CheckCircle2,
  },
];
const [active, setActive] = useState(0);

useEffect(() => {
  const timer = setInterval(() => {
    setActive((prev) => (prev + 1) % steps.length);
  }, 2500);

  return () => clearInterval(timer);
}, []);
<div className="space-y-6">

{steps.map((step,index)=>{

const Icon=step.icon;

return(

<div
key={step.title}
className="flex items-center gap-5"
>

<div
className={`rounded-xl p-4 ${
index<=active
? "bg-cyan-500 text-black"
: "bg-white/10 text-white"
}`}
>

<Icon size={24}/>

</div>

<div className="flex-1">

<div className="flex justify-between">

<span className="text-white">
{step.title}
</span>

<span className="text-cyan-300">

{index<active
? "Done"
: index===active
? "Running"
: "Waiting"}

</span>

</div>

<div className="mt-2 h-2 rounded-full bg-white/10">

<motion.div

animate={{
width:index<=active?"100%":"0%"
}}

transition={{
duration:1
}}

className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-500"
/>

</div>

</div>

</div>

)

})}

</div>

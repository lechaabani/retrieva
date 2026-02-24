"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface SliderProps {
  label?: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  showValue?: boolean;
  className?: string;
}

export function Slider({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  showValue = true,
  className,
}: SliderProps) {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className={cn("space-y-2", className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between">
          {label && (
            <label className="text-sm font-medium text-text-primary">
              {label}
            </label>
          )}
          {showValue && (
            <span className="text-sm font-mono text-text-secondary">
              {value}
            </span>
          )}
        </div>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 rounded-full appearance-none cursor-pointer bg-surface-3 accent-brand-600"
        style={{
          background: `linear-gradient(to right, #4f46e5 0%, #4f46e5 ${percentage}%, var(--surface-3) ${percentage}%, var(--surface-3) 100%)`,
        }}
      />
    </div>
  );
}

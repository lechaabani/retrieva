"use client";

import React, { useState, useEffect } from "react";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Toggle } from "@/components/ui/toggle";

interface PluginConfigPanelProps {
  configSchema: Record<string, any>;
  currentConfig: Record<string, any>;
  onSave: (config: Record<string, any>) => Promise<void>;
}

function inferFieldType(schema: any): string {
  if (schema.type) return schema.type;
  if (typeof schema.default === "boolean") return "boolean";
  if (typeof schema.default === "number") return "integer";
  return "string";
}

export function PluginConfigPanel({
  configSchema,
  currentConfig,
  onSave,
}: PluginConfigPanelProps) {
  const [values, setValues] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const initial: Record<string, any> = {};
    for (const [key, schema] of Object.entries(configSchema)) {
      initial[key] =
        currentConfig[key] !== undefined
          ? currentConfig[key]
          : (schema as any).default ?? "";
    }
    setValues(initial);
  }, [configSchema, currentConfig]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await onSave(values);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  const fields = Object.entries(configSchema);

  if (fields.length === 0) {
    return (
      <p className="text-sm text-text-muted py-4">
        This plugin has no configurable options.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {fields.map(([key, schema]) => {
        const fieldSchema = schema as Record<string, any>;
        const fieldType = inferFieldType(fieldSchema);
        const label = fieldSchema.title || key;
        const description = fieldSchema.description || "";

        if (fieldType === "boolean") {
          return (
            <Toggle
              key={key}
              label={label}
              description={description}
              checked={!!values[key]}
              onChange={(checked) =>
                setValues((prev) => ({ ...prev, [key]: checked }))
              }
            />
          );
        }

        if (fieldType === "integer" || fieldType === "number") {
          return (
            <div key={key}>
              <Input
                label={label}
                type="number"
                value={values[key] ?? ""}
                onChange={(e) =>
                  setValues((prev) => ({
                    ...prev,
                    [key]: e.target.value === "" ? "" : Number(e.target.value),
                  }))
                }
              />
              {description && (
                <p className="text-xs text-text-muted mt-1">{description}</p>
              )}
            </div>
          );
        }

        return (
          <div key={key}>
            <Input
              label={label}
              type="text"
              value={values[key] ?? ""}
              placeholder={fieldSchema.default ?? ""}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, [key]: e.target.value }))
              }
            />
            {description && (
              <p className="text-xs text-text-muted mt-1">{description}</p>
            )}
          </div>
        );
      })}

      <div className="flex items-center gap-3 pt-2">
        <Button
          icon={<Save size={16} />}
          onClick={handleSave}
          loading={saving}
        >
          Save Configuration
        </Button>
        {saved && (
          <span className="text-sm text-emerald-600 dark:text-emerald-400">
            Saved successfully
          </span>
        )}
      </div>
    </div>
  );
}

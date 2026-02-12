"use client";

import { useState } from "react";
import {
  PseudocodeStep,
  FieldMappingStep,
  LookupJoinStep,
  BusinessRuleStep,
  FilterStep,
  CalculationStep,
  OutputStep,
} from "@/lib/api";
import FieldMappingTable from "./FieldMappingTable";
import StepComment from "./StepComment";

interface Props {
  step: PseudocodeStep;
  onComment: (stepId: string, comment: string) => void;
  existingComment?: string;
}

function StepIcon({ type }: { type: string }) {
  const iconClass = "w-5 h-5";

  switch (type) {
    case "field_mapping":
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
        </svg>
      );
    case "lookup_join":
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      );
    case "business_rule":
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      );
    case "filter":
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
        </svg>
      );
    case "calculation":
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      );
    case "output":
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
      );
    default:
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      );
  }
}

function FieldMappingContent({ step }: { step: FieldMappingStep }) {
  return <FieldMappingTable mappings={step.mappings} />;
}

function LookupJoinContent({ step }: { step: LookupJoinStep }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-600">Join:</span>
        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">
          {step.join_key.source}
        </code>
        <span className="text-gray-400">=</span>
        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">
          {step.join_key.lookup}
        </code>
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-600">Output:</span>
        <code className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-xs">
          {step.output_field}
        </code>
      </div>

      {step.filter && (
        <div className="text-sm">
          <span className="text-gray-600">Filter:</span>{" "}
          <span className="text-gray-700">{step.filter}</span>
        </div>
      )}

      {step.sample_mappings && step.sample_mappings.length > 0 && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs font-medium text-gray-600 mb-2">
            Sample mappings from your data:
          </p>
          <div className="space-y-1">
            {step.sample_mappings.slice(0, 5).map((m, idx) => (
              <div key={idx} className="text-xs text-gray-700">
                {m.from} → {m.to}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BusinessRuleContent({ step }: { step: BusinessRuleStep }) {
  return (
    <div className="space-y-2">
      {step.rules.map((rule, idx) => (
        <div key={idx} className="flex items-start gap-2 text-sm">
          <span className="text-gray-400 mt-0.5">•</span>
          <div>
            <span className="text-gray-600">IF</span>{" "}
            <code className="bg-gray-100 px-1 rounded text-xs">
              {rule.condition}
            </code>{" "}
            <span className="text-gray-600">→</span>{" "}
            <code className="bg-blue-50 text-blue-700 px-1 rounded text-xs">
              {rule.action}
            </code>
          </div>
        </div>
      ))}
    </div>
  );
}

function FilterContent({ step }: { step: FilterStep }) {
  return (
    <div className="text-sm">
      <span className="text-gray-600">
        {step.exclude ? "Exclude rows where:" : "Include rows where:"}
      </span>
      <code className="ml-2 bg-gray-100 px-1.5 py-0.5 rounded text-xs">
        {step.condition}
      </code>
    </div>
  );
}

function CalculationContent({ step }: { step: CalculationStep }) {
  return (
    <div className="text-sm space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-gray-600">Output field:</span>
        <code className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-xs">
          {step.output_field}
        </code>
      </div>
      <div className="flex items-start gap-2">
        <span className="text-gray-600">Formula:</span>
        <code className="bg-gray-100 px-2 py-1 rounded text-xs">
          {step.formula}
        </code>
      </div>
    </div>
  );
}

function OutputContent({ step }: { step: OutputStep }) {
  return (
    <div className="text-sm space-y-1">
      <div>
        <span className="text-gray-600">Format:</span>{" "}
        <span className="text-gray-700">{step.format}</span>
      </div>
      <div>
        <span className="text-gray-600">Destination:</span>{" "}
        <span className="text-gray-700">{step.destination}</span>
      </div>
    </div>
  );
}

export default function StepCard({ step, onComment, existingComment }: Props) {
  const [isExpanded, setIsExpanded] = useState(true);

  function renderContent() {
    switch (step.type) {
      case "field_mapping":
        return <FieldMappingContent step={step} />;
      case "lookup_join":
        return <LookupJoinContent step={step} />;
      case "business_rule":
        return <BusinessRuleContent step={step} />;
      case "filter":
        return <FilterContent step={step} />;
      case "calculation":
        return <CalculationContent step={step} />;
      case "output":
        return <OutputContent step={step} />;
      default: {
        // Handle unknown step types gracefully
        const unknownStep = step as { description?: string };
        return (
          <p className="text-sm text-gray-600">
            {unknownStep.description || "No details available"}
          </p>
        );
      }
    }
  }

  const typeLabels: Record<string, string> = {
    field_mapping: "Field Mapping",
    lookup_join: "Lookup Join",
    business_rule: "Business Rules",
    filter: "Filter",
    calculation: "Calculation",
    output: "Output",
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-700 rounded text-xs font-medium">
            {step.id}
          </span>
          <div className="text-gray-600">
            <StepIcon type={step.type} />
          </div>
          <div className="text-left">
            <span className="font-medium text-gray-900">{step.title}</span>
            <span className="ml-2 text-xs text-gray-500">
              {typeLabels[step.type] || step.type}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {existingComment && (
            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">
              Has feedback
            </span>
          )}
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${
              isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-100">
          {step.description && (
            <p className="text-sm text-gray-600 mb-3">{step.description}</p>
          )}
          {renderContent()}
          <StepComment
            stepId={step.id}
            onComment={onComment}
            existingComment={existingComment}
          />
        </div>
      )}
    </div>
  );
}

"use client";

import { FieldMapping } from "@/lib/api";

interface Props {
  mappings: FieldMapping[];
  initialLimit?: number;
}

export default function FieldMappingTable({
  mappings,
  initialLimit = 5,
}: Props) {
  const showAll = mappings.length <= initialLimit + 2;
  const displayMappings = showAll ? mappings : mappings.slice(0, initialLimit);
  const remaining = mappings.length - initialLimit;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 pr-4 font-medium text-gray-600">
              Source Column
            </th>
            <th className="text-center py-2 px-2 font-medium text-gray-400 w-8">

            </th>
            <th className="text-left py-2 pl-4 font-medium text-gray-600">
              Target Field
            </th>
            <th className="text-left py-2 pl-4 font-medium text-gray-600">
              Transform
            </th>
          </tr>
        </thead>
        <tbody>
          {displayMappings.map((mapping, idx) => (
            <tr
              key={idx}
              className="border-b border-gray-100 last:border-0 hover:bg-gray-50"
            >
              <td className="py-2 pr-4">
                <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                  {mapping.source}
                </code>
              </td>
              <td className="py-2 px-2 text-center text-gray-400">→</td>
              <td className="py-2 pl-4">
                <code className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                  {mapping.target}
                </code>
              </td>
              <td className="py-2 pl-4 text-gray-500 text-xs">
                {mapping.transform === "direct" && "Direct"}
                {mapping.transform === "rename" && "Rename"}
                {mapping.transform === "formula" && (
                  <span title={mapping.formula}>Formula</span>
                )}
                {mapping.transform === "lookup" && "Lookup"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {!showAll && (
        <p className="text-xs text-gray-500 mt-2 pl-1">
          ... and {remaining} more mapping{remaining > 1 ? "s" : ""}
        </p>
      )}
    </div>
  );
}

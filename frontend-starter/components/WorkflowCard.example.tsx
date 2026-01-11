/**
 * Example usage of the WorkflowCard component
 * This demonstrates how to use the component for the Edit Draft page
 */

import { WorkflowCards } from './WorkflowCard';

export function EditDraftWorkflowExample() {
  const workflowCards = [
    {
      title: 'Draft Basics',
      status: 'done' as const,
      details: 'Draft basics complete',
      updatedAt: '09/01/2026, 17:12:27',
    },
    {
      title: 'Images',
      status: 'not_started' as const,
    },
    {
      title: 'Interlinking',
      status: 'in_progress' as const,
      details: 'Analysis completed',
      updatedAt: '11/01/2026, 13:31:16',
    },
    {
      title: 'Polish and Human in the Loop',
      status: 'done' as const,
      details: 'Content polished',
      updatedAt: '11/01/2026, 13:41:41',
      isActive: true, // This card is highlighted
    },
    {
      title: 'Final QA',
      status: 'done' as const,
    },
    {
      title: 'Publish',
      status: 'not_started' as const,
    },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <a href="/drafts" className="text-blue-600 hover:underline">
          &lt;-- Back to Drafts
        </a>
      </div>

      <h1 className="text-3xl font-bold mb-2">Edit Draft</h1>
      <p className="text-gray-600 mb-6">
        Guided workflow for polish, interlinking, QA, and publishing.
      </p>

      {/* Workflow Cards */}
      <WorkflowCards cards={workflowCards} />

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 mt-6">
        <button className="px-4 py-2 border border-blue-500 text-blue-600 rounded hover:bg-blue-50">
          Request Approval
        </button>
        <button className="px-4 py-2 border border-blue-500 text-blue-600 rounded hover:bg-blue-50">
          Regenerate
        </button>
        <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Save Draft
        </button>
      </div>
    </div>
  );
}


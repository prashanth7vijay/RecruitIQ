import { useState } from "react";
import { Link } from "react-router-dom";
import {
  useOffersForApplication,
  useOfferApprovalSteps,
  useCreateOffer,
  useSubmitOfferForApproval,
  useApproveOfferStep,
  useAcceptOffer,
  useDeclineOffer,
} from "./useOffers";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";

const STATUS_LABEL = {
  draft: "Draft",
  pending_approval: "Pending approval",
  sent: "Sent",
  accepted: "Accepted",
  rejected: "Declined",
  withdrawn: "Withdrawn",
};

export function OfferPanel({ applicationId }) {
  const { data: offers } = useOffersForApplication(applicationId);
  const createOffer = useCreateOffer(applicationId);
  const submitForApproval = useSubmitOfferForApproval(applicationId);
  const approveStep = useApproveOfferStep(applicationId);
  const acceptOffer = useAcceptOffer(applicationId);
  const declineOffer = useDeclineOffer(applicationId);
  const [salary, setSalary] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const offer = offers?.[0]; // one offer per application in this simple flow
  const { data: approvalSteps } = useOfferApprovalSteps(offer?.id, offer?.status === "pending_approval");

  async function handleSubmitForApproval() {
    setSubmitError(null);
    try {
      await submitForApproval.mutateAsync({ offerId: offer.id });
    } catch (err) {
      setSubmitError(
        err.response?.data?.error?.message ??
          "Could not submit for approval. An admin may need to configure an approval chain first."
      );
    }
  }

  if (!offers) return null;

  if (!offer) {
    return showForm ? (
      <div className="mt-2 flex items-end gap-2 border-t border-ink-100 pt-2">
        <Input
          id="salary"
          label="Salary"
          type="number"
          value={salary}
          onChange={(e) => setSalary(e.target.value)}
          className="w-28"
        />
        <Button
          onClick={() => createOffer.mutate({ salaryOffered: salary })}
          disabled={createOffer.isPending || !salary}
        >
          {createOffer.isPending ? "Creating…" : "Create offer"}
        </Button>
      </div>
    ) : (
      <button
        onClick={() => setShowForm(true)}
        className="mt-2 block text-xs font-medium text-ink-500 hover:text-ink-700"
      >
        Make an offer
      </button>
    );
  }

  return (
    <div className="mt-2 border-t border-ink-100 pt-2 text-xs">
      <p className="font-medium text-ink-700">
        Offer: ${Number(offer.salary_offered).toLocaleString()} — {STATUS_LABEL[offer.status]}
      </p>

      {offer.status === "draft" && (
        <button
          onClick={handleSubmitForApproval}
          disabled={submitForApproval.isPending}
          className="mt-1 font-medium text-signal-600 hover:text-signal-700"
        >
          {submitForApproval.isPending ? "Submitting…" : "Submit for approval"}
        </button>
      )}
      {submitError && <p className="mt-1 text-xs text-red-600">{submitError}</p>}

      {offer.status === "pending_approval" && approvalSteps?.map((step) => (
        <div key={step.id} className="mt-1 flex items-center justify-between">
          <span className="capitalize text-ink-500">{(step.approver_role_name ?? "unassigned").replace("_", " ")}</span>
          {step.status === "pending" ? (
            <button
              onClick={() => approveStep.mutate({ offerId: offer.id, stepId: step.id })}
              disabled={approveStep.isPending}
              className="font-medium text-signal-600 hover:text-signal-700"
            >
              Approve
            </button>
          ) : (
            <span className="text-ink-400">{step.status}</span>
          )}
        </div>
      ))}

      {offer.status === "sent" && (
        <div className="mt-1 flex gap-3">
          <button
            onClick={() => acceptOffer.mutate(offer.id)}
            disabled={acceptOffer.isPending}
            className="font-medium text-signal-600 hover:text-signal-700"
          >
            Mark accepted
          </button>
          <button
            onClick={() => declineOffer.mutate(offer.id)}
            disabled={declineOffer.isPending}
            className="font-medium text-red-500 hover:text-red-600"
          >
            Mark declined
          </button>
        </div>
      )}
      {offer.status === "accepted" && (
        <Link to={`/onboarding/${applicationId}`} className="mt-1 block font-medium text-signal-600 hover:text-signal-700">
          View onboarding →
        </Link>
      )}
    </div>
  );
}

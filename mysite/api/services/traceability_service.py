class TraceabilityService:
    @staticmethod
    def get_batch_history(batch):
        """
        UC 11.4: Consulter historique complet d’un lot
        """
        logs = batch.traceability_logs.all().order_by('created_at')
        history = []
        for log in logs:
            history.append({
                "action": log.action_type,
                "date": log.created_at,
                "performer": log.performed_by.phone,
                "metadata": log.metadata
            })
        return history

    @staticmethod
    def get_value_chain(batch):
        """
        UC 11.5: Visualiser chaîne de valeur
        Recursive trace of inputs/outputs.
        """
        # Simple implementation for now
        history = TraceabilityService.get_batch_history(batch)
        # Add transport and transformation info
        transports = batch.transports.all()
        transformations = batch.used_in_transformations.all()
        
        return {
            "batch_info": {
                "id": batch.unique_code,
                "parcel": batch.parcel.name,
                "farmer": batch.farmer.phone
            },
            "history": history,
            "logistics": [
                {"type": "transport", "from": t.from_location, "to": t.to_location, "status": t.status} 
                for t in transports
            ]
        }

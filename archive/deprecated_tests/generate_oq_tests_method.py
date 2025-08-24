    @step
    async def generate_oq_tests(
        self,
        ctx: Context,
        ev: OQTestGenerationEvent
    ) -> OQTestSuiteEvent:
        """
        Generate OQ test suite based on planning and agent results.
        
        Args:
            ctx: Workflow context
            ev: OQ test generation event with all required context
            
        Returns:
            OQTestSuiteEvent with generated test suite
        """
        self.logger.info("🧪 Starting OQ test generation")
        
        # We now receive the OQTestGenerationEvent directly with all required context
        oq_generation_event = ev
        
        # Run OQ generation workflow
        from src.agents.oq_generator.workflow import OQTestGenerationWorkflow
        
        oq_workflow = OQTestGenerationWorkflow(
            llm=self.llm,
            timeout=600,  # 10 minutes
            verbose=self.verbose,
            enable_validation=True,
            oq_generation_event=oq_generation_event
        )
        
        try:
            self.logger.info("Running OQ test generation workflow...")
            oq_result = await oq_workflow.run()
            
            # Extract result
            if hasattr(oq_result, "result"):
                oq_data = oq_result.result
            else:
                oq_data = oq_result
            
            # Check if generation was successful
            if oq_data.get("status") == "completed_successfully":
                # Extract the OQ test suite event
                oq_event = oq_data.get("full_event")
                if oq_event and isinstance(oq_event, OQTestSuiteEvent):
                    self.logger.info(
                        f"✅ Generated {oq_event.test_suite.total_test_count} OQ tests successfully"
                    )
                    return oq_event
                else:
                    # Create event from data
                    raise ValueError("OQ generation completed but no valid event returned")
            else:
                # Handle consultation required or error
                consultation = oq_data.get("consultation", {})
                raise RuntimeError(
                    f"OQ generation requires consultation: {consultation.get('consultation_type', 'unknown')}"
                )
                
        except Exception as e:
            self.logger.error(f"OQ generation failed: {e}")
            # Re-raise to trigger consultation
            raise
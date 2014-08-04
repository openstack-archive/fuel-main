update_templ = """Update os on {0}

         Scenario:
            1. Revert  environment {1}
            2. Upload tarball
            3. Check that it uploaded
            4. Extract data
            5. Get available releases
            6. Run update script
            7. Check that new release appears
            8. Put new release into cluster
            9. Run cluster update
            10. Run OSTF
            11. Create snapshot

        """

rollback_templ = """Rollback os on {0}

         Scenario:
            1. Revert  patched environment {1}
            2. Get release ids
            2. Identify release id for rollback
            3. Run rollback
            4. Check that rollback was successful
            5. Run OSTF
            6. Create snapshot

        """
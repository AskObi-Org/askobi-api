# Style guide: repositories

Representative files:

- `src/repositories/user_repository.py`

## Project-specific conventions

- Repositories are small classes and accept `AsyncSession`.
- They commit and refresh inside repository methods.
- Return types are `Optional[Model]` for getters.

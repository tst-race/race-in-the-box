# RACE in the Box (RiB)

Templates are a way of templatizing portions of the generated docker-compose for RiB system.

## Note on Brittleness

Because we are using CLI args to insert or not insert portions of this and doing from yml to python to yaml, things can break by even moving spaces.

i.e. tmpfs.yml needs 6 spaces for the subsections below the main volume. This is not good and needs to be fixed.

**Note**: This isn't breaking anything, just CAN break if we are not careful.

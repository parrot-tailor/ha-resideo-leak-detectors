# How to contribute

Third-party patches are essential for keeping this project great. We want to
keep it as easy as possible to contribute changes. There are a few guidelines
that we need contributors to follow so that we can have a chance to keep on top
of things.

## Getting Started

* Make sure you have a [GitHub account](https://github.com/join).
* Submit a new issue to the project's repository, assuming one does not already
exist.
* Clearly describe the problem. If it's a bug, include the steps needed to
reproduce it.
* Include the earliest version of the project that you know has the issue.
* Fork the repository on GitHub.

## Making Changes

* Create a topic branch from where you want to base your work; you usually want
to branch off `main`.
* To quickly create a topic branch based on the `main` branch, run

      git checkout -b my-contribution

  Please refrain from working directly on the `main` branch.
* Make commits of logical units, rebasing against the `main` branch when needed.
Please refrain from submitting pull requests with merge commits.
* Check for unnecessary whitespace with `git diff --check` before committing.
* Make sure your commit messages are in the proper format.

      (gh-123) adds an example commit message

      Before this patch, the contributor must imagine how a proper commit
      message should look based on a description rather than an example.

      This patch adds an example commit message. The subject line contains a
      real-life statement, potentially with an issue number from the issue
      tracker or a tag such as '(docs).' The body describes the behavior
      without the patch, why it's a problem, and how the patch fixes the
      problem when applied.

* Make sure you have added the necessary tests for your changes.
* Run _all_ the tests and ensure they're passing.

For trivial changes, creating a new issue is not always necessary. In this
case, starting the first line of a commit with `(docs)` or `(maint)` instead of
an issue number is appropriate.

## Submitting Changes

* Push your changes to a topic branch in your fork of the repository.
* Submit a pull request to the origin repository.
* Update your issue to note that you have submitted your changes and are ready
for a code review.
* Include a link to the pull request in the issue.

## Additional Resources

* [GitHub Documentation](https://docs.github.com/en)
* [GitHub Pull Requests Documentation](https://docs.github.com/en/pull-requests)

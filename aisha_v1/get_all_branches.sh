for branch in $(git branch -r | grep -v '\->'); do
  git branch --track "${branch#origin/}" "$branch" 2>/dev/null
done
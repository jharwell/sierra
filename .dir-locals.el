;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")

((python-mode
  (eval progn
        (require 'python-mode-init)
        (require 'editing-init)
        (add-to-list 'projectile-globally-ignored-directories "docs/_build/")
        (add-to-list 'projectile-globally-ignored-directories "sierra.egg-info/")
        (add-to-list 'projectile-globally-ignored-directories "dist/")
        (add-to-list 'projectile-globally-ignored-directories ".pytype/")
        (add-to-list 'projectile-globally-ignored-directories ".mypy_cache/")
        (add-to-list 'projectile-globally-ignored-file-suffixes "*.html")
        (add-to-list 'projectile-globally-ignored-file-suffixes "*.pickle")
        (add-to-list 'projectile-globally-ignored-file-suffixes "*.pkl")
        (add-to-list 'projectile-globally-ignored-file-suffixes "*.png")
        (add-to-list 'projectile-globally-ignored-file-suffixes "*.doctree")
        (add-to-list 'grep-find-ignored-directories "docs/_build/")
        (add-to-list 'grep-find-ignored-directories "sierra.egg-info/")
        (add-to-list 'grep-find-ignored-directories "dist/")
        (add-to-list 'grep-find-ignored-files "*.html")
        (add-to-list 'grep-find-ignored-files "*.txt")
        (add-to-list 'grep-find-ignored-files "*.png")
        (add-to-list 'grep-find-ignored-files "*.doctree")
        (add-to-list 'grep-find-ignored-files "*.pickle")
        )))


;;; end of .dir-locals.el

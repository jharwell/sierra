;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")

((python-mode
  (eval progn
        (require 'python-mode-init)
        (add-to-list 'projectile-globally-ignored-directories "docs/_build/")
        (add-to-list 'projectile-globally-ignored-directories ".pytype/")
        (add-to-list 'projectile-globally-ignored-directories ".mypy_cache/")
        (add-to-list 'projectile-globally-ignored-file-suffixes ".html")
        (add-to-list 'projectile-globally-ignored-file-suffixes ".pickle")
        (add-to-list 'projectile-globally-ignored-file-suffixes ".pkl")
        )))


;;; end of .dir-locals.el

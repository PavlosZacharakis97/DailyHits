import { useEffect, useId, useRef } from 'react'
import styles from './Modal.module.css'

/**
 * Native <dialog>: focus trap, Esc to close and an inert page come for free.
 * Renders as a bottom sheet on phones.
 */
export function Modal({ open, onClose, title, children, wide = false }) {
  const ref = useRef(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      className={`${styles.dialog} ${wide ? styles.wide : ''}`}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(e) => {
        // A click on the backdrop (the dialog element itself) closes it.
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className={styles.body}>
        <header className={styles.head}>
          <h2 id={titleId} className={styles.title}>
            {title}
          </h2>
          <button type="button" className={styles.close} onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>
        {children}
      </div>
    </dialog>
  )
}

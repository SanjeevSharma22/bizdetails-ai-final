import React, { useEffect, useRef } from 'react';

const ensureHttps = (url = '') => {
  if (!url) return '';
  try {
    // Allow bare domains like "linkedin.com/company/123"
    if (!/^https?:\/\//i.test(url)) return `https://${url}`;
    return url;
  } catch {
    return '';
  }
};

const domainToFavicon = (domain = '') =>
  domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : '';

export function CompanyDetailsPanel({ company, onClose }) {
  const isOpen = !!company;
  const panelRef = useRef(null);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  const linkedInHref = ensureHttps(company?.linkedin_url);
  const siteHref = company?.domain
    ? ensureHttps(
        company.domain.includes('.') ? company.domain : `${company.domain}.com`
      )
    : '';

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/50 transition-opacity duration-300 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
        aria-hidden={!isOpen}
      />

      {/* Slide-over panel */}
      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label="Company details"
        className={`fixed top-0 right-0 h-full w-96 max-w-full bg-white shadow-lg transform transition-transform duration-300 border-l ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            {company?.domain ? (
              <img
                src={domainToFavicon(company.domain)}
                alt=""
                className="h-6 w-6 rounded"
              />
            ) : null}
            <h2 className="text-lg font-medium">Details</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-600 hover:text-gray-800"
            aria-label="Close panel"
          >
            ✕
          </button>
        </div>

        {isOpen && (
          <div className="p-4 space-y-3 text-sm">
            <p>
              <strong className="text-primary">Name:</strong>{' '}
              {company?.name || company?.['Original Name'] || 'N/A'}
            </p>

            <p className="break-all">
              <strong className="text-primary">Domain:</strong>{' '}
              {company?.domain ? (
                siteHref ? (
                  <a
                    href={siteHref}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                    title="Open website"
                  >
                    {company.domain}
                  </a>
                ) : (
                  company.domain
                )
              ) : (
                'N/A'
              )}
            </p>

            <p>
              <strong className="text-primary">Headquarters:</strong>{' '}
              {company?.hq || 'N/A'}
            </p>

            <p>
              <strong className="text-primary">Country / Region:</strong>{' '}
              {company?.countries || company?.country || 'N/A'}
            </p>

            <p>
              <strong className="text-primary">Industry:</strong>{' '}
              {company?.industry || 'N/A'}
            </p>

            {company?.subindustry ? (
              <p>
                <strong className="text-primary">Subindustry:</strong>{' '}
                {company.subindustry}
              </p>
            ) : null}

            {company?.size ? (
              <p>
                <strong className="text-primary">Company Size:</strong>{' '}
                {company.size}
              </p>
            ) : null}

            {company?.['Legal Name'] ? (
              <p className="break-all">
                <strong className="text-primary">Legal Name:</strong>{' '}
                {company['Legal Name']}
              </p>
            ) : null}

            {company?.slug ? (
              <p className="break-all">
                <strong className="text-primary">Slug:</strong> {company.slug}
              </p>
            ) : null}

            {company?.keywords_cntxt ? (
              <p className="break-words">
                <strong className="text-primary">Keywords:</strong>{' '}
                {company.keywords_cntxt}
              </p>
            ) : null}

            <p className="break-all">
              <strong className="text-primary">LinkedIn:</strong>{' '}
              {company?.linkedin_url ? (
                linkedInHref ? (
                  <a
                    href={linkedInHref}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                    title="Open LinkedIn"
                  >
                    {company.linkedin_url}
                  </a>
                ) : (
                  company.linkedin_url
                )
              ) : (
                'N/A'
              )}
            </p>
          </div>
        )}
      </aside>
    </>
  );
}
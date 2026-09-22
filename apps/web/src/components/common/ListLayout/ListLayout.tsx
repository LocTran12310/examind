/**
 * A list screen that fills the viewport: header on top, the content (a DataTable or MasterDetail)
 * takes the remaining height so only the table body scrolls. Below ~30rem of height the page
 * itself scrolls instead of squeezing the table.
 */
export function ListLayout({ header, children }: { header?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex min-h-[30rem] flex-1 flex-col">
      {header}
      <div className="min-h-0 flex-1">{children}</div>
    </div>
  );
}

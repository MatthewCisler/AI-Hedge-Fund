import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";
import { fetchOrders, fetchQueuedTrades, fetchTrades } from "@/lib/api";

export default async function TradesPage() {
  const [orders, queued, trades] = await Promise.all([fetchOrders(), fetchQueuedTrades(), fetchTrades()]);

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Trades</p>
          <h1>Orders, fills, and queued activity</h1>
        </div>
      </div>
      <div className="dashboardGrid">
        <SectionCard title="Recent trades" subtitle="Filled paper-trading activity">
          <div className="list">
            {trades.length ? (
              trades.map((trade) => (
                <div key={trade.id} className="listRow">
                  <div>
                    <strong>
                      {trade.side.toUpperCase()} {trade.ticker}
                    </strong>
                    <p className="muted">{trade.notes ?? "Paper fill"}</p>
                  </div>
                  <div className="alignRight">
                    <strong>${(trade.quantity * trade.fill_price).toFixed(2)}</strong>
                    <p className="muted">
                      {trade.quantity} @ ${trade.fill_price.toFixed(2)}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="muted">No fills yet.</p>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Queued trades" subtitle="Approved ideas waiting for the next market open">
          <div className="list">
            {queued.length ? (
              queued.map((trade) => (
                <div key={trade.id} className="listRow">
                  <strong>
                    {trade.side.toUpperCase()} {trade.ticker}
                  </strong>
                  <p className="muted">{trade.reason}</p>
                </div>
              ))
            ) : (
              <p className="muted">No queued trades.</p>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Orders" subtitle="Alpaca paper order submissions and rejections">
          <div className="list">
            {orders.length ? (
              orders.map((order) => (
                <div key={order.id} className="listRow">
                  <div>
                    <strong>
                      {order.side.toUpperCase()} {order.ticker}
                    </strong>
                    <p className="muted">{order.broker_order_id ?? order.rejection_reason ?? "Local paper adapter"}</p>
                  </div>
                  <div className="alignRight">
                    <strong>{order.status}</strong>
                    <p className="muted">{order.quantity} shares</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="muted">No orders yet.</p>
            )}
          </div>
        </SectionCard>
      </div>
    </AppLayout>
  );
}

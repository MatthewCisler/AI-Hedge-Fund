import { AppLayout } from "@/components/layout";
import { SectionCard } from "@/components/cards";
import { ActionButton } from "@/components/action-button";
import { OrderForm } from "@/components/trade-workflow";
import { fetchOrders, fetchPortfolios, fetchQueuedTrades, fetchTrades } from "@/lib/api";
import { formatChicagoTimestamp } from "@/lib/format";

export default async function TradesPage() {
  const [orders, queued, trades, portfolios] = await Promise.all([fetchOrders(), fetchQueuedTrades(), fetchTrades(), fetchPortfolios()]);

  return (
    <AppLayout>
      <div className="pageHeader">
        <div>
          <p className="eyebrow">Trades</p>
          <h1>Orders, fills, and queued activity</h1>
        </div>
        <div className="pageActions">
          <ActionButton label="Sync Alpaca paper orders" path="/trades/orders/sync" variant="primary" />
        </div>
      </div>
      <SectionCard title="Submit a paper order" subtitle="Every order is checked by deterministic portfolio rules before queueing or submission">
        {portfolios.length ? <OrderForm portfolios={portfolios} /> : <p className="emptyState">Create a portfolio before submitting an order.</p>}
      </SectionCard>
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

        <SectionCard title="Orders" subtitle="Broker submissions stay pending until a confirmed Alpaca paper fill is synchronized">
          <div className="list">
            {orders.length ? (
              orders.map((order) => (
                <div key={order.id} className="listRow">
                  <div>
                    <strong>
                      {order.side.toUpperCase()} {order.ticker}
                    </strong>
                    <p className="muted">{order.broker_order_id ?? order.rejection_reason ?? "Local paper adapter"}</p>
                    <p className="muted">Submitted {order.submitted_at ? formatChicagoTimestamp(order.submitted_at) : "pending"}{order.filled_at ? ` · Filled ${formatChicagoTimestamp(order.filled_at)}` : ""}</p>
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

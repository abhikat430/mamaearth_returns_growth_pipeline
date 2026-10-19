-- Run each query after schema.sql and seed_data.sql.
-- a) Expected raw result: total_orders=180, total_revenue=99860.20, avg_order_value=554.78
SELECT COUNT(*) AS total_orders,
 ROUND(SUM(o.quantity*p.price*(1-COALESCE(o.discount_pct,0)/100.0)),2) AS total_revenue,
 ROUND(AVG(o.quantity*p.price*(1-COALESCE(o.discount_pct,0)/100.0)),2) AS avg_order_value
FROM orders o JOIN products p USING(product_id);

-- b) Expected: 180, 165, 15
SELECT COUNT(*) AS all_orders, COUNT(rating) AS rated_orders,
 COUNT(*)-COUNT(rating) AS unrated_orders FROM orders;

-- c1) Expected: C045, Vihaan
SELECT c.customer_id,c.name FROM customers c LEFT JOIN orders o USING(customer_id)
GROUP BY c.customer_id,c.name HAVING COUNT(o.order_id)=0;
-- c2) Independent confirmation: C045, Vihaan
SELECT customer_id,name FROM customers
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);

-- d) Expected high-return cities: Jaipur, Lucknow, Bangalore
SELECT c.city, COUNT(*) AS total_orders, SUM(o.returned) AS returned_orders,
 ROUND(100.0*SUM(o.returned)/COUNT(*),1) AS return_rate_pct
FROM orders o JOIN customers c USING(customer_id)
GROUP BY c.city HAVING return_rate_pct > 20 ORDER BY return_rate_pct DESC;

-- e) Tie-break customer_id ASC makes rankings deterministic for equal spend.
SELECT c.customer_id,c.name,
 ROUND(SUM(o.quantity*p.price*(1-COALESCE(o.discount_pct,0)/100.0)),2) AS total_spend
FROM orders o JOIN products p USING(product_id) JOIN customers c USING(customer_id)
GROUP BY c.customer_id,c.name ORDER BY total_spend DESC,c.customer_id ASC LIMIT 5;
SELECT c.customer_id,c.name,
 ROUND(SUM(o.quantity*p.price*(1-COALESCE(o.discount_pct,0)/100.0)),2) AS total_spend
FROM orders o JOIN products p USING(product_id) JOIN customers c USING(customer_id)
GROUP BY c.customer_id,c.name ORDER BY total_spend DESC,c.customer_id ASC LIMIT 3 OFFSET 2;

-- f) Three-table join retained for end-to-end validation.
SELECT p.category, COUNT(*) AS order_count,
 ROUND(SUM(o.quantity*p.price*(1-COALESCE(o.discount_pct,0)/100.0)),2) AS category_revenue
FROM orders o JOIN products p USING(product_id) JOIN customers c USING(customer_id)
GROUP BY p.category ORDER BY category_revenue DESC;

-- g) Expected 10 rows
SELECT customer_id,name FROM customers WHERE name LIKE 'A%' ORDER BY customer_id;
-- h) Expected Ad, Organic, Referral, Social
SELECT DISTINCT acquisition_source FROM customers ORDER BY acquisition_source;
-- i) Run once; SQLite will error if rerun after column exists.
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);
UPDATE customers SET loyalty_tier = CASE WHEN city_tier=1 THEN 'Gold' ELSE 'Silver' END;
SELECT loyalty_tier,COUNT(*) FROM customers GROUP BY loyalty_tier ORDER BY loyalty_tier;

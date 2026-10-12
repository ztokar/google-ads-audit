# Audit query library

Each block is one `search` tool call. Replace `{START}` / `{END}` with `YYYY-MM-DD` dates and `{CID}` with the digits-only customer ID. `DATE` below means the condition `segments.date BETWEEN '{START}' AND '{END}'`.

If a field errors, call `get_resource_metadata` for that resource and adjust.

---

## Q1 — Account snapshot
- resource: `customer`
- fields: `customer.descriptive_name, customer.currency_code, customer.time_zone, customer.auto_tagging_enabled, customer.optimization_score, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.conversions_value, metrics.all_conversions`
- conditions: `DATE`

## Q2 — Campaigns
- resource: `campaign`
- fields: `campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, campaign.bidding_strategy_type, campaign_budget.amount_micros, campaign.network_settings.target_google_search, campaign.network_settings.target_search_network, campaign.network_settings.target_content_network, campaign.geo_target_type_setting.positive_geo_target_type, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.conversions_value, metrics.search_impression_share, metrics.search_budget_lost_impression_share, metrics.search_rank_lost_impression_share`
- conditions: `campaign.status != 'REMOVED'`, `DATE`
- orderings: `metrics.cost_micros DESC`

## Q3 — Conversion actions (configuration)
- resource: `conversion_action`
- fields: `conversion_action.id, conversion_action.name, conversion_action.status, conversion_action.type, conversion_action.category, conversion_action.origin, conversion_action.primary_for_goal, conversion_action.include_in_conversions_metric, conversion_action.counting_type, conversion_action.click_through_lookback_window_days, conversion_action.attribution_model_settings.attribution_model, conversion_action.value_settings.default_value, conversion_action.value_settings.always_use_default_value`
- conditions: `conversion_action.status != 'REMOVED'`

## Q4 — Conversions by action (volume)
- resource: `customer`
- fields: `segments.conversion_action_name, segments.conversion_action_category, metrics.conversions, metrics.all_conversions, metrics.conversions_value`
- conditions: `DATE`

## Q5 — Search partners vs Google search
- resource: `campaign`
- fields: `campaign.name, segments.ad_network_type, metrics.cost_micros, metrics.clicks, metrics.conversions`
- conditions: `campaign.advertising_channel_type = 'SEARCH'`, `campaign.status != 'REMOVED'`, `DATE`

## Q6 — Location targets
- resource: `campaign_criterion`
- fields: `campaign.name, campaign_criterion.location.geo_target_constant, campaign_criterion.negative, campaign_criterion.bid_modifier`
- conditions: `campaign_criterion.type = 'LOCATION'`, `campaign.status != 'REMOVED'`

## Q7 — Keywords + Quality Score
- resource: `keyword_view`
- fields: `campaign.name, ad_group.name, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.status, ad_group_criterion.quality_info.quality_score, ad_group_criterion.quality_info.creative_quality_score, ad_group_criterion.quality_info.post_click_quality_score, ad_group_criterion.quality_info.search_predicted_ctr, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions`
- conditions: `ad_group_criterion.status != 'REMOVED'`, `DATE`
- orderings: `metrics.cost_micros DESC`
- limit: `1000`

## Q8 — Non-converting search terms (waste)
- resource: `search_term_view`
- fields: `search_term_view.search_term, search_term_view.status, campaign.name, ad_group.name, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions`
- conditions: `metrics.conversions = 0`, `metrics.cost_micros > 0`, `DATE`
- orderings: `metrics.cost_micros DESC`
- limit: `500`

## Q8b — Converting search terms (for comparison and keyword ideas)
- same as Q8 with conditions `metrics.conversions > 0`, `DATE`; limit `200`

## Q9 — Campaign-level negative keywords
- resource: `campaign_criterion`
- fields: `campaign.name, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type`
- conditions: `campaign_criterion.negative = TRUE`, `campaign_criterion.type = 'KEYWORD'`, `campaign.status != 'REMOVED'`

## Q10 — Negative keyword lists and where they're applied
- resource: `campaign_shared_set`
- fields: `campaign.name, shared_set.name, shared_set.type, shared_set.member_count, campaign_shared_set.status`
- conditions: `shared_set.type = 'NEGATIVE_KEYWORDS'`, `campaign.status != 'REMOVED'`

## Q10b — Account-level negatives (lists and placement exclusions)
- resource: `customer_negative_criterion`
- fields: `customer_negative_criterion.type, customer_negative_criterion.negative_keyword_list.shared_set, customer_negative_criterion.placement.url`
- Count these toward negative coverage before failing the "no negatives" check.

## Q10c — Ad-group negatives
- resource: `ad_group_criterion`
- fields: `campaign.id, ad_group.id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type`
- conditions: `ad_group_criterion.negative = TRUE`, `ad_group_criterion.type = 'KEYWORD'`, `ad_group_criterion.status != 'REMOVED'`

## Q10d — Shared negative list contents
- resource: `shared_criterion`
- fields: `shared_set.id, shared_set.name, shared_criterion.keyword.text, shared_criterion.keyword.match_type`
- conditions: `shared_set.type = 'NEGATIVE_KEYWORDS'`
- Join list IDs to campaign assignments and account-level list references before claiming coverage.

## Q11 — Ads, ad strength, approval
- resource: `ad_group_ad`
- fields: `campaign.name, ad_group.name, ad_group_ad.ad.id, ad_group_ad.ad.type, ad_group_ad.status, ad_group_ad.ad_strength, ad_group_ad.policy_summary.approval_status, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions`
- conditions: `ad_group_ad.status != 'REMOVED'`, `campaign.status != 'REMOVED'`, `DATE`

## Q12 — Ad groups (to find groups with 0–1 ads)
- resource: `ad_group`
- fields: `campaign.name, ad_group.id, ad_group.name, ad_group.status, metrics.cost_micros, metrics.conversions`
- conditions: `ad_group.status = 'ENABLED'`, `campaign.status = 'ENABLED'`, `DATE`
- Compare against Q11 (enabled RSAs per ad group).

## Q13 — Assets (extensions)
Account level:
- resource: `customer_asset`
- fields: `customer_asset.field_type, customer_asset.status, asset.type`
- conditions: `customer_asset.status != 'REMOVED'`

Campaign level:
- resource: `campaign_asset`
- fields: `campaign.name, campaign.status, campaign_asset.field_type, campaign_asset.status, asset.type`
- conditions: `campaign_asset.status != 'REMOVED'`, `campaign.status != 'REMOVED'`

## Q14 — Performance Max asset groups
- resource: `asset_group`
- fields: `campaign.name, asset_group.name, asset_group.status, asset_group.ad_strength, metrics.cost_micros, metrics.conversions, metrics.conversions_value`
- conditions: `asset_group.status != 'REMOVED'`, `DATE`

## Q15 — Device
- resource: `campaign`
- fields: `campaign.name, segments.device, metrics.cost_micros, metrics.clicks, metrics.conversions, metrics.conversions_value`
- conditions: `campaign.status != 'REMOVED'`, `DATE`

## Q16 — Geography (user location)
- resource: `user_location_view`
- fields: `user_location_view.country_criterion_id, user_location_view.targeting_location, segments.geo_target_region, metrics.cost_micros, metrics.clicks, metrics.conversions`
- conditions: `DATE`
- orderings: `metrics.cost_micros DESC`
- limit: `200`
- Interpret location results alongside Q2 targeting mode and Q6 exclusions. Do not diagnose leakage from this boolean alone.

## Q20 — Customer and campaign conversion goals
- resource: `customer_conversion_goal`
- fields: `customer_conversion_goal.category, customer_conversion_goal.origin, customer_conversion_goal.biddable`
- resource: `campaign_conversion_goal`
- fields: `campaign.id, campaign_conversion_goal.category, campaign_conversion_goal.origin, campaign_conversion_goal.biddable`
- Inspect custom conversion goals and campaign goal configuration through resource metadata when present; primary action flags alone are insufficient to diagnose inappropriate bidding goals.

## Q21 — Search-term reporting coverage
- resource: `search_term_view`
- fields: `metrics.cost_micros, metrics.clicks, metrics.conversions`
- conditions: `DATE`, `campaign.advertising_channel_type = 'SEARCH'`
- No term dimension or row limit. Compare against the Search campaign totals from Q2 for the same period. If the aggregate is unsupported, report coverage as unavailable rather than extrapolating from Q8's limited sample.

## Q17 — Day of week / hour
- resource: `campaign`
- fields: `segments.day_of_week, segments.hour, metrics.cost_micros, metrics.clicks, metrics.conversions`
- conditions: `campaign.status != 'REMOVED'`, `DATE`

## Q18 — Change history (last 30 days only — API limit)
- resource: `change_event`
- fields: `change_event.change_date_time, change_event.change_resource_type, change_event.resource_change_operation, change_event.user_email, change_event.client_type, campaign.name`
- conditions: `change_event.change_date_time >= '{RECENT_START_TIMESTAMP}'`, `change_event.change_date_time < '{NOW_TIMESTAMP}'`
- Use full timestamps in the account time zone within the most recent 30 days, independently of the audit period. Use a 29-day lookback to avoid the boundary.
- orderings: `change_event.change_date_time DESC`
- limit: `1000` (must be ≤ 10000)

## Q19 — Google's open recommendations (context only)
- resource: `recommendation`
- fields: `recommendation.type, recommendation.campaign, recommendation.dismissed`
- conditions: `recommendation.dismissed = FALSE`
- Don't parrot these — use them only as secondary signals.


## Q22 — Performance Max search terms
- resource: `campaign_search_term_view`
- fields: `campaign.name, campaign_search_term_view.search_term, metrics.cost_micros, metrics.clicks, metrics.conversions, metrics.conversions_value`
- conditions: `DATE`, `campaign.advertising_channel_type = 'PERFORMANCE_MAX'`, `metrics.cost_micros > 0`
- orderings: `metrics.cost_micros DESC`
- limit: `500`
- Named terms are incomplete and cover search inventory only. Compare within channel; do not label non-converting spend as waste or infer all PMax traffic from this sample.

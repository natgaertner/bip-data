drop view if exists candidate_join_contest;
create view candidate_join_contest(co_electoral_district_id, office, electorate_specifications, write_in, special, number_elected, contest_type, co_id, co_source, state, electoral_district_name, type, electoral_district_type, co_election_key, filing_closed_data, number_voting_for, custom_ballot_heading, ballot_placement, primary_party, co_election_id, co_identifier, partisan, office_level, ed_matched, filed_mailing_addres, ca_election_key, name, phone, mailing_address, facebook_url, youtube, email, candidate_url, ca_source, google_plus_url, twitter_name, incumbent, party, wiki_word, ca_identifier, ca_id, biography, photo_url) as (select co.*, ca.* from contest as co join candidate_in_contest as cic on co.id=cic.contest_id join candidate as ca on cic.candidate_id = ca.id);
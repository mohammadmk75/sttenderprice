import streamlit as st
import pandas as pd
import numpy as np

def format_number_input(label,key):
    user_input = st.text_input(label, key=key)
    try:
        # Remove commas and convert to float
        value = float(user_input.replace(",", ""))
        formatted_value = f"{value:,.0f}"
        st.markdown(f"<p style='color: orange;'>{formatted_value}</p>", unsafe_allow_html=True)
        return value
    except ValueError:
        st.error("Please enter a valid number.")
        return 0.0
logo_path = 'logo.jpg'
st.image(logo_path, width = 300)
# App Title
st.title("Tender Evaluation App")


# Tender Estimation Inputs
st.header("Tender Estimation Details")
pb = format_number_input("Enter the Tender Estimation Value (P):" , key="pb" ) # Adds a thousands separator)
beta = st.number_input("Enter the Beta Value (β):", min_value=0.0,step=0.1, format="%.2f")
gama = st.number_input("Enter the Gama Value (γ):", min_value=0.0, step=0.1, format="%.2f")


tender_category = st.selectbox(
    "What is The Tender Category",
    ("1399", "1394")
)

st.write("You selected:", tender_category)
# Calculate P0
if tender_category == '1399':
    if pb > 0 and beta > 0 and gama > 0:
        p0 = pb * beta * gama
        # st.write(f"Calculated On-Time Estimation Value (P0): {p0}")
        formatted_p0 = f"{p0:,.2f}"  # Format P0 with thousands separator and 2 decimal places
        st.markdown(
        f"<p style='color: green;'>Calculated On-Time Estimation Value (P0): {formatted_p0}</p>",
        unsafe_allow_html=True
        )

        # Ask if Tender is Two-Step
        two_step = st.checkbox("Is the Tender a Two-Step Process?")

        # Company Data Entry
        st.header("Enter Company Details")
        cont_count = st.number_input("Enter the Number of Tender Contributors:", min_value=1, step=1)
        if cont_count < 3:
            st.error("At least 3 contributors are required for the tender process.")
        else:
            # Ask for Tender Importance
            importance = st.selectbox("Select the Tender Importance:", ['Medium', 'High', 'Very High'])

            # Set importance factor based on the number of contributors
            if 3 <= cont_count <= 6:
                importance_factors = {'Medium': 1.1, 'High': 1.0, 'Very High': 0.9}
            elif 7 <= cont_count <= 10:
                importance_factors = {'Medium': 1.3, 'High': 1.2, 'Very High': 1.1}
            else:
                importance_factors = {'Medium': 1.5, 'High': 1.4, 'Very High': 1.3}

            importance_factor = importance_factors[importance]
            st.write(f"Importance Factor: {importance_factor}")

            # Initialize data storage for companies
            companies = {}

            for i in range(1, cont_count + 1):
                st.subheader(f"Company {i} Details")
                company_name = st.text_input(f"Enter Company {i} Name:", key=f"name_{i}")
                company_factor = st.number_input(f"Enter the Scale factor of {company_name} :", min_value=0.0,step=0.1, format="%.2f",key=f"impact_{i}")
                estimate_pi_price = p0 * company_factor
                # st.write(f'The estimated price for {company_name} is:') 
                # st.write(estimate_pi_price)
                formatted_price = f"{estimate_pi_price:,.2f}"  # Format the price with commas and 2 decimal places
                st.markdown(f"<p style='color: orange;'>The estimated price for {company_name} is: {formatted_price}</p>", unsafe_allow_html=True)
                # Ask for Technical Score Only If Two-Step
                tech_score = None
                if two_step:
                    tech_score = st.number_input(f"Enter {company_name}'s Technical Score (t):", min_value=0.0, max_value=100.0, key=f"t_{i}")

                if company_name and estimate_pi_price > 0:
                    xi_value = (estimate_pi_price / p0) * 100
                    companies[company_name] = {
                        'Price Scale' : company_factor,
                        'pi': estimate_pi_price,
                        'xi': xi_value,
                        't': tech_score,
                        'status': 'Pending',
                        'score': None
                    }

            # Ask for Impact Factor Once if Two-Step
            if two_step:
                impact_factor = st.number_input("Enter the Technical Score Impact Factor:", min_value=0.0)

            if st.button("Evaluate"):
                # Calculate Standard Deviation
                xi_values = [data['xi'] for data in companies.values()] + [100]
                std = np.std(xi_values, ddof=1)
                st.write(f"Standard Deviation (STD): {std:.2f}")

                # Calculate LCL and UCL
                lcl = 87 + 0.4 * min(std, 10)
                ucl = 130 - 0.25 * min(std, 20)
                st.write(f"LCL: {lcl:.2f}, UCL: {ucl:.2f}")

                # Update Status Based on LCL and UCL
                for company_name, data in companies.items():
                    if data['xi'] < lcl or data['xi'] > ucl:
                        data['status'] = 'Unacceptable Price'
                    else:
                        data['status'] = 'Acceptable Price'

                # Adjust Status If 65% of Companies Have Unacceptable Status
                unacceptable_count = sum(1 for data in companies.values() if data['status'] == 'Unacceptable Price')
                total_companies = len(companies)
                if unacceptable_count / total_companies >= 0.65:
                    for company_name in companies:
                        companies[company_name]['status'] = 'Acceptable Price'
                    st.warning("65% or more companies have unacceptable prices. All companies' statuses are now marked as 'Acceptable Price'.")
                    below_lcl_count = sum(1 for data in companies.values() if data['xi'] < lcl)
                    total_companies = len(companies)
                    below_lcl_percentage = (below_lcl_count / total_companies) * 100

                    if below_lcl_percentage >= 35:
                        st.warning(f"35% or more of the companies have prices below the LCL. Please enter a new tender estimation value.")

                df = pd.DataFrame.from_dict(companies, orient='index')
                st.dataframe(df)
                # Recalculate Acceptable Companies
                acceptable_companies = {k: v for k, v in companies.items() if v['status'] == 'Acceptable Price'}

                if acceptable_companies:
                    # Calculate Mean of xi values
                    xi_values = [data['xi'] for data in acceptable_companies.values()] + [100]
                    mean_xi = np.mean(xi_values)
                    st.write(f"Mean of xi values: {mean_xi:.4f}")

                    # Calculate Unacceptable Threshold
                    unacceptable_threshold = 1.10 * mean_xi if mean_xi > 115 else 1.25 * mean_xi
                    st.write(f"Unacceptable xi threshold (B Value): {unacceptable_threshold:.4f}")

                    # Mark Companies as Unacceptable Based on Threshold
                    for company_name, data in companies.items():
                        if data['xi'] > unacceptable_threshold:
                            data['status'] = 'Unacceptable Price'

                    # Recalculate Acceptable Companies
                    acceptable_companies = {k: v for k, v in companies.items() if v['status'] == 'Acceptable Price'}

                    # Recalculate Mean and Std
                    if acceptable_companies:
                        xi_values_acceptable = [data['xi'] for data in acceptable_companies.values()] + [100]
                        m_prime = np.mean(xi_values_acceptable)
                        s_prime = np.std(xi_values_acceptable, ddof=1)
                        st.write(f"New Mean (m') of xi for acceptable companies: {m_prime:.4f}")
                        st.write(f"New Std (s') of xi for acceptable companies: {s_prime:.4f}")

                        # Check for Final Acceptability
                        lower_bound = m_prime - importance_factor * s_prime
                        upper_bound = m_prime + importance_factor * s_prime
                        st.write(f"Lower Bound is: {lower_bound:.4f}")
                        st.write(f"Upper Bound is {upper_bound:.4f}")

                        for company_name, data in acceptable_companies.items():
                            if not (lower_bound <= data['xi'] <= upper_bound):
                                data['status'] = 'Unacceptable Price'

                        # Recalculate Acceptable Companies After Final Check
                        acceptable_companies = {k: v for k, v in companies.items() if v['status'] == 'Acceptable Price'}

                if acceptable_companies:
                    # Calculate Final Scores
                    for company_name, data in acceptable_companies.items():
                        if two_step and data['t'] is not None:
                            try:
                                data['score'] = (100 * data['pi']) / (100 - (impact_factor * (100 - data['t'])))
                            except ZeroDivisionError:
                                data['score'] = float('inf')
                        else:
                            data['score'] = data['pi']

                    # Determine the Winner
                    winner = min(acceptable_companies, key=lambda x: acceptable_companies[x]['score'])
                    st.success(f"The winner is **{winner}** with a score of **{acceptable_companies[winner]['score']:.2f}**")
                else:
                    st.error("No acceptable prices found.")

                # Display Final Results
                result_df = pd.DataFrame.from_dict(companies, orient='index')
                st.dataframe(result_df)

else:
        if pb > 0 and beta > 0 and gama > 0:
            p0 = pb * beta * gama
            formatted_p0 = f"{p0:,.2f}"  # Format P0 with thousands separator and 2 decimal places
            st.markdown(
        f"<p style='color: green;'>Calculated On-Time Estimation Value (P0): {formatted_p0}</p>",
        unsafe_allow_html=True
        )

        # Ask if Tender is Two-Step
        two_step = st.checkbox("Is the Tender a Two-Step Process?")

        # Company Data Entry
        st.header("Enter Company Details")
        cont_count = st.number_input("Enter the Number of Tender Contributors:", min_value=1, step=1)
        if cont_count < 3:
            st.error("At least 3 contributors are required for the tender process.")
        else:
            # Ask for Tender Importance
            importance = st.selectbox("Select the Tender Importance:", ['Medium', 'High', 'Very High'])

            # Set importance factor based on the number of contributors
            if 3 <= cont_count <= 6:
                importance_factors = {'Medium': 1.1, 'High': 1.0, 'Very High': 0.9}
            elif 7 <= cont_count <= 10:
                importance_factors = {'Medium': 1.3, 'High': 1.2, 'Very High': 1.1}
            else:
                importance_factors = {'Medium': 1.5, 'High': 1.4, 'Very High': 1.3}

            importance_factor = importance_factors[importance]
            st.write(f"Importance Factor: {importance_factor}")

            # Initialize data storage for companies
            companies = {}

            for i in range(1, cont_count + 1):
                st.subheader(f"Company {i} Details")
                company_name = st.text_input(f"Enter Company {i} Name:", key=f"name_{i}")
                company_factor = st.number_input(f"Enter the Company Scale Factor of {company_name} :", min_value=0.0,step=0.1, format="%.2f",key=f"impact_{i}")
                estimate_pi_price = p0 * company_factor
                # st.write(f'The estimated price for {company_name} is:') 
                # st.write(estimate_pi_price)
                formatted_price = f"{estimate_pi_price:,.2f}"  # Format the price with commas and 2 decimal places
                st.markdown(f"<p style='color: orange;'>The estimated price for {company_name} is: {formatted_price}</p>", unsafe_allow_html=True)
                tech_score = None
                if two_step:
                    tech_score = st.number_input(f"Enter {company_name}'s Technical Score (t):", min_value=0.0, max_value=100.0, key=f"t_{i}")

                if company_name and estimate_pi_price > 0:
                    xi_value = (estimate_pi_price / p0) * 100
                    companies[company_name] = {
                        'Company Price Scale Factor' : company_factor,
                        'pi': estimate_pi_price,
                        'xi': xi_value,
                        't': tech_score,
                        'status': 'Acceptable Price',
                        'score': None
                    }

            # Ask for Impact Factor Once if Two-Step
            if two_step:
                impact_factor = st.number_input("Enter the Impact Factor for Technical Score:", min_value=0.0)

            if st.button("Evaluate"):
                # Calculate Standard Deviation
                xi_values = [data['xi'] for data in companies.values()] + [100]
                std = np.std(xi_values, ddof=1)
                st.write(f"Standard Deviation (STD): {std:.2f}")

                # Calculate LCL and UCL
                # lcl = 87 + 0.4 * min(std, 10)
                # ucl = 130 - 0.25 * min(std, 20)
                # st.write(f"LCL: {lcl:.2f}, UCL: {ucl:.2f}")

                # Update Status Based on LCL and UCL
                # for company_name, data in companies.items():
                #     if data['xi'] < lcl or data['xi'] > ucl:
                #         data['status'] = 'Unacceptable Price'
                #     else:
                #         data['status'] = 'Acceptable Price'

                # Adjust Status If 65% of Companies Have Unacceptable Status
                unacceptable_count = sum(1 for data in companies.values() if data['status'] == 'Unacceptable Price')
                total_companies = len(companies)
                if unacceptable_count / total_companies >= 0.65:
                    for company_name in companies:
                        companies[company_name]['status'] = 'Acceptable Price'
                    st.warning("65% or more companies have unacceptable prices. All companies' statuses are now marked as 'Acceptable Price'.")
                    # below_lcl_count = sum(1 for data in companies.values() if data['xi'] < lcl)
                    # total_companies = len(companies)
                    # below_lcl_percentage = (below_lcl_count / total_companies) * 100

                    # if below_lcl_percentage >= 35:
                    #     st.warning(f"35% or more of the companies have prices below the LCL. Please enter a new tender estimation value.")

                df = pd.DataFrame.from_dict(companies, orient='index')
                st.dataframe(df)
                # Recalculate Acceptable Companies
                acceptable_companies = {k: v for k, v in companies.items() if v['status'] == 'Acceptable Price'}

                if acceptable_companies:
                    # Calculate Mean of xi values
                    xi_values = [data['xi'] for data in acceptable_companies.values()] + [100]
                    mean_xi = np.mean(xi_values)
                    st.write(f"Mean of xi values: {mean_xi:.4f}")

                    # Calculate Unacceptable Threshold
                    unacceptable_threshold = 1.10 * mean_xi if mean_xi > 115 else 1.25 * mean_xi
                    st.write(f"Unacceptable xi threshold (B Value): {unacceptable_threshold:.4f}")

                    # Mark Companies as Unacceptable Based on Threshold
                    for company_name, data in companies.items():
                        if data['xi'] > unacceptable_threshold:
                            data['status'] = 'Unacceptable Price'

                    # Recalculate Acceptable Companies
                    acceptable_companies = {k: v for k, v in companies.items() if v['status'] == 'Acceptable Price'}

                    # Recalculate Mean and Std
                    if acceptable_companies:
                        xi_values_acceptable = [data['xi'] for data in acceptable_companies.values()] + [100]
                        m_prime = np.mean(xi_values_acceptable)
                        s_prime = np.std(xi_values_acceptable, ddof=1)
                        st.write(f"New Mean (m') of xi for acceptable companies: {m_prime:.4f}")
                        st.write(f"New Std (s') of xi for acceptable companies: {s_prime:.4f}")

                        # Check for Final Acceptability
                        lower_bound = m_prime - importance_factor * s_prime
                        upper_bound = m_prime + importance_factor * s_prime
                        st.write(f"Lower Bound is: {lower_bound:.4f}")
                        st.write(f"Upper Bound is {upper_bound:.4f}")

                        for company_name, data in acceptable_companies.items():
                            if not (lower_bound <= data['xi'] <= upper_bound):
                                data['status'] = 'Unacceptable Price'

                        # Recalculate Acceptable Companies After Final Check
                        acceptable_companies = {k: v for k, v in companies.items() if v['status'] == 'Acceptable Price'}

                if acceptable_companies:
                    # Calculate Final Scores
                    for company_name, data in acceptable_companies.items():
                        if two_step and data['t'] is not None:
                            try:
                                data['score'] = (100 * data['pi']) / (100 - (impact_factor * (100 - data['t'])))
                            except ZeroDivisionError:
                                data['score'] = float('inf')
                        else:
                            data['score'] = data['pi']

                    # Determine the Winner
                    winner = min(acceptable_companies, key=lambda x: acceptable_companies[x]['score'])
                    st.success(f"The winner is **{winner}** with a score of **{acceptable_companies[winner]['score']:.2f}**")
                else:
                    st.error("No acceptable prices found.")

                # Display Final Results
                result_df = pd.DataFrame.from_dict(companies, orient='index')
                st.dataframe(result_df)
